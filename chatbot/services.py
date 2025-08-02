import requests
import json
import time
from django.conf import settings
from django.utils.translation import gettext as _
from .models import ChatSession, ChatMessage, ChatConfiguration
from lawyers.models import Lawyer
from django.utils import timezone


class DeepSeekAIService:
    """Service for integrating with DeepSeek AI API"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_system_prompt(self, lawyer, language='ru'):
        """Generate system prompt for the lawyer's chatbot"""
        specialties = lawyer.get_specialties_display()
        specialties_str = ", ".join(specialties) if specialties else "юридические услуги"
        
        system_prompts = {
            'ru': f"""Вы юридический помощник для {lawyer.full_name} в Кыргызстане.

ПРАВИЛА:
- Отвечайте только на русском языке
- Предоставляйте только общую правовую информацию, никогда не давайте конкретных юридических советов
- Всегда рекомендуйте консультацию с юристом для конкретных случаев  
- Вежливо собирайте контактную информацию посетителя
- Будьте профессиональными и полезными
- Если не уверены, скажите "Я свяжу вас с нашим юристом"

СПЕЦИАЛИЗАЦИИ: {specialties_str}

ОТВЕТЫ ДОЛЖНЫ:
1. Отвечать на общие правовые вопросы
2. Объяснять правовые процессы в Кыргызстане  
3. Предоставлять примерные расценки по запросу
4. Собирать: имя, телефон, email, описание дела
5. Предлагать запись на консультацию

ПЛАТА ЗА КОНСУЛЬТАЦИЮ: {lawyer.consultation_fee} сом

ОБРАЗЦЫ ОТВЕТОВ:
- "Здравствуйте! Я помощник юриста {lawyer.full_name}. Как могу помочь?"
- "Для вашего случая потребуется консультация. Могу записать вас на встречу?"
- "Такие дела обычно стоят от X до Y сом. Оставьте контакты для точной консультации."
""",
            
            'ky': f"""Сиз {lawyer.full_name}дын Кыргызстандагы юридикалык жардамчысыз.

ЭРЕЖЕЛЕР:
- Кыргыз тилинде гана жооп бериңиз
- Жалпы укуктук маалыматты гана бериңиз, конкретүү укуктук кеңештерди бербеңиз
- Конкретүү иштер үчүн юрист менен кеңешүүнү сунуштаңыз
- Келүүчүнүн байланыш маалыматын сылык менен чогултуңуз
- Кесипкөй жана пайдалуу болуңуз
- Эгер ишенимиңиз жок болсо, "Мен сизди биздин юрист менен байланыштырам" деңиз

АДИСТИКТЕР: {specialties_str}

ЖООПТОРУҢУЗ:
1. Жалпы укуктук суроолорго жооп бериңиз
2. Кыргызстандагы укуктук процесстерди түшүндүрүңүз
3. Суроо боюнча баа болжолдорун бериңиз
4. Топтоңуз: аты, телефону, email, иштин сыпаттамасы
5. Консультацияга жазылууну сунуштаңыз

КОНСУЛЬТАЦИЯ АКЫСЫ: {lawyer.consultation_fee} сом
""",
            
            'en': f"""You are a legal assistant for {lawyer.full_name} in Kyrgyzstan.

RULES:
- Respond only in English
- Provide general legal information only, never specific legal advice
- Always recommend consulting with the lawyer for specific cases
- Politely collect visitor contact information
- Be professional and helpful
- If unsure, say "I'll connect you with our lawyer"

SPECIALTIES: {specialties_str}

RESPONSES SHOULD:
1. Answer general legal questions
2. Explain legal processes in Kyrgyzstan
3. Provide fee estimates when asked
4. Collect: name, phone, email, case description
5. Offer consultation scheduling

CONSULTATION FEE: {lawyer.consultation_fee} som

SAMPLE RESPONSES:
- "Hello! I'm {lawyer.full_name}'s legal assistant. How can I help you?"
- "For your case, a consultation would be required. Can I schedule you for a meeting?"
- "Such cases usually cost from X to Y som. Please leave your contacts for an accurate consultation."
"""
        }
        
        return system_prompts.get(language, system_prompts['ru'])
    
    def send_message(self, session, user_message, config=None):
        """Send message to DeepSeek AI and get response"""
        start_time = time.time()
        
        try:
            if not config:
                config = session.lawyer.chat_config
            
            # Get conversation history
            messages = self.get_conversation_history(session, config)
            
            # Add user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare API request
            payload = {
                "model": config.ai_model,
                "messages": messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "stream": False
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract AI response
            ai_response = result['choices'][0]['message']['content']
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message
            )
            
            # Save AI response
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=ai_response,
                ai_model=config.ai_model,
                response_time_ms=response_time_ms,
                tokens_used=result.get('usage', {}).get('total_tokens', 0)
            )
            
            # Update session activity
            session.save()
            
            return {
                'success': True,
                'response': ai_response,
                'response_time_ms': response_time_ms
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'response': self.get_fallback_response(session.language)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'response': self.get_fallback_response(session.language)
            }
    
    def get_conversation_history(self, session, config):
        """Get conversation history for context"""
        messages = []
        
        # Add system prompt
        system_prompt = self.get_system_prompt(session.lawyer, session.language)
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add recent conversation history (last 10 messages)
        recent_messages = session.messages.order_by('created_at')[-10:]
        
        for msg in recent_messages:
            if msg.message_type == 'user':
                messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.message_type == 'ai':
                messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        return messages
    
    def get_fallback_response(self, language='ru'):
        """Get fallback response when AI is unavailable"""
        fallback_responses = {
            'ru': "Извините, в данный момент я не могу ответить. Пожалуйста, оставьте ваши контактные данные, и наш юрист свяжется с вами в ближайшее время.",
            'ky': "Кечириңиз, азыр жооп бере албайм. Сураныч, байланыш маалыматыңызды калтырыңыз, биздин юрист сиз менен жакын арада байланышат.",
            'en': "Sorry, I cannot respond at the moment. Please leave your contact information and our lawyer will get back to you soon."
        }
        return fallback_responses.get(language, fallback_responses['ru'])
    
    def analyze_intent(self, message, language='ru'):
        """Analyze user message intent for lead capture"""
        message_lower = message.lower()
        
        # Keywords for different intents
        consultation_keywords = {
            'ru': ['консультация', 'встреча', 'прием', 'записаться', 'встретиться'],
            'ky': ['консультация', 'жолугушуу', 'кабыл алуу', 'жазылуу'],
            'en': ['consultation', 'meeting', 'appointment', 'schedule', 'book']
        }
        
        contact_keywords = {
            'ru': ['телефон', 'контакт', 'связь', 'номер', 'email'],
            'ky': ['телефон', 'байланыш', 'номер', 'email'],
            'en': ['phone', 'contact', 'number', 'email', 'call']
        }
        
        # Check for consultation request
        if any(keyword in message_lower for keyword in consultation_keywords.get(language, [])):
            return 'consultation_request'
        
        # Check for contact sharing
        if any(keyword in message_lower for keyword in contact_keywords.get(language, [])):
            return 'contact_sharing'
        
        # Check for phone number or email in message
        import re
        if re.search(r'\+?\d{10,}', message) or re.search(r'\S+@\S+\.\S+', message):
            return 'contact_provided'
        
        return 'general_inquiry'


class ChatbotService:
    """Main service for chatbot operations"""
    
    def __init__(self):
        self.ai_service = DeepSeekAIService()
    
    def start_session(self, lawyer, visitor_ip=None, user_agent=None, referrer=None):
        """Start a new chat session"""
        session = ChatSession.objects.create(
            lawyer=lawyer,
            visitor_ip=visitor_ip,
            user_agent=user_agent,
            referrer=referrer,
            language=lawyer.primary_language
        )
        
        # Send welcome message
        config = lawyer.chat_config
        welcome_message = config.get_welcome_message(session.language)
        
        ChatMessage.objects.create(
            session=session,
            message_type='ai',
            content=welcome_message
        )
        
        return session
    
    def process_message(self, session, message):
        """Process incoming message and generate response"""
        # Get chat configuration
        try:
            config = session.lawyer.chat_config
        except ChatConfiguration.DoesNotExist:
            # Create default configuration
            config = ChatConfiguration.objects.create(
                lawyer=session.lawyer,
                system_prompt=self.ai_service.get_system_prompt(session.lawyer, session.language)
            )
        
        # Check office hours if enabled
        if config.office_hours_enabled and not config.is_office_hours():
            offline_response = config.offline_message or self.ai_service.get_fallback_response(session.language)
            
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=offline_response
            )
            
            return {
                'success': True,
                'response': offline_response,
                'is_offline': True
            }
        
        # Analyze message intent
        intent = self.ai_service.analyze_intent(message, session.language)
        
        # Process message with AI
        result = self.ai_service.send_message(session, message, config)
        
        # Handle lead capture based on intent
        if intent == 'contact_provided':
            self.extract_contact_info(session, message)
        elif intent == 'consultation_request':
            session.consultation_requested = True
            session.save()
        
        return result
    
    def extract_contact_info(self, session, message):
        """Extract contact information from message"""
        import re
        
        # Extract phone number
        phone_match = re.search(r'\+?(\d{10,})', message)
        if phone_match and not session.visitor_phone:
            session.visitor_phone = phone_match.group()
        
        # Extract email
        email_match = re.search(r'\S+@\S+\.\S+', message)
        if email_match and not session.visitor_email:
            session.visitor_email = email_match.group()
        
        # Extract name (simple heuristic)
        if not session.visitor_name:
            # Look for "меня зовут", "my name is", etc.
            name_patterns = [
                r'меня зовут (\w+)',
                r'my name is (\w+)',
                r'менин атым (\w+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    session.visitor_name = match.group(1)
                    break
        
        session.save()
    
    def end_session(self, session):
        """End chat session"""
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save()
        
        # Create lead if contact info was collected
        if session.is_lead:
            self.create_lead_from_session(session)
    
    def create_lead_from_session(self, session):
        """Create lead from chat session"""
        from leads.models import Lead
        
        # Extract case description from conversation
        conversation = session.messages.filter(
            message_type='user'
        ).values_list('content', flat=True)
        
        case_description = ' '.join(conversation)
        
        lead = Lead.objects.create(
            lawyer=session.lawyer,
            name=session.visitor_name or f"Chat Visitor ({session.visitor_ip})",
            email=session.visitor_email or '',
            phone=session.visitor_phone or '',
            case_description=case_description[:1000],  # Limit length
            legal_category=session.legal_category or '',
            source='chatbot',
            ip_address=session.visitor_ip,
            user_agent=session.user_agent
        )
        
        return lead 
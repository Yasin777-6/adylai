from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.conf import settings
import json
import requests
import uuid
from datetime import datetime
from lawyers.models import Lawyer
from leads.models import Lead
from .models import ChatSession, ChatMessage


@method_decorator(csrf_exempt, name='dispatch')
class StartChatAPIView(View):
    """Initialize a new chat session with a lawyer's AI assistant"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            lawyer_slug = data.get('lawyer_slug')
            visitor_name = data.get('visitor_name', 'Anonymous')
            
            # Get lawyer
            lawyer = get_object_or_404(Lawyer, domain_slug=lawyer_slug)
            
            # Create chat session
            session = ChatSession.objects.create(
                lawyer=lawyer,
                session_id=str(uuid.uuid4()),
                visitor_info={'name': visitor_name},
                status='active',
                language='ru',  # Default to Russian
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            
            # Welcome message
            welcome_message = f"""Здравствуйте! Я помощник юриста {lawyer.user.get_full_name()}. 

Я могу помочь вам с:
🔸 Консультациями по правовым вопросам
🔸 Информацией о наших услугах 
🔸 Записью на встречу с юристом
🔸 Предварительной оценкой вашего дела

Как дела? Чем могу помочь?"""
            
            # Save welcome message
            ChatMessage.objects.create(
                session=session,
                message_type='assistant',
                content=welcome_message,
                ai_model='system'
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.session_id,
                'message': welcome_message,
                'lawyer_name': lawyer.user.get_full_name()
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class SendMessageAPIView(View):
    """Send message to AI and get response"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'success': False, 'error': 'Message is required'})
            
            # Get chat session
            session = get_object_or_404(ChatSession, session_id=session_id)
            lawyer = session.lawyer
            
            # Save user message
            user_chat_message = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message
            )
            
            # Check if user is asking for contact/meeting
            contact_keywords = ['встреча', 'консультация', 'записаться', 'телефон', 'контакт', 'адрес', 'цена', 'стоимость']
            asking_for_contact = any(keyword in user_message.lower() for keyword in contact_keywords)
            
            # Prepare system prompt for DeepSeek
            system_prompt = f"""Вы - профессиональный помощник юриста {lawyer.user.get_full_name()} в Кыргызстане.

ИНФОРМАЦИЯ О ЮРИСТЕ:
- Имя: {lawyer.user.get_full_name()}
- Опыт: {lawyer.years_experience} лет
- Специализации: {', '.join(lawyer.specialties) if lawyer.specialties else 'Общая юридическая практика'}
- Телефон: {lawyer.phone}
- Email: {lawyer.user.email}
- Стоимость консультации: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом

ПРАВИЛА:
1. Отвечайте на русском языке профессионально и дружелюбно
2. Предоставляйте общую правовую информацию, но не конкретные юридические советы
3. Направляйте клиентов к юристу для детальной консультации
4. Если клиент хочет записаться на встречу, попросите его контактные данные
5. Будьте краткими, но информативными (максимум 3-4 предложения)
6. Если не знаете ответ, честно скажите об этом и предложите консультацию с юристом

ЦЕЛЬ: Помочь клиенту и записать его на консультацию к юристу."""

            # Call DeepSeek API
            try:
                response = self.get_ai_response(system_prompt, user_message, session)
                ai_message = response.get('content', 'Извините, произошла ошибка. Пожалуйста, свяжитесь с нами напрямую.')
                
                # Save AI response
                ChatMessage.objects.create(
                    session=session,
                    message_type='assistant', 
                    content=ai_message,
                    ai_model='deepseek-chat',
                    response_time_ms=response.get('response_time', 0),
                    tokens_used=response.get('tokens_used', 0)
                )
                
                # Check if we need to collect contact info
                should_collect_contact = asking_for_contact and not session.visitor_info.get('phone')
                
                response_data = {
                    'success': True,
                    'message': ai_message,
                    'should_collect_contact': should_collect_contact
                }
                
                if should_collect_contact:
                    response_data['contact_form'] = {
                        'title': 'Записаться на консультацию',
                        'subtitle': f'Оставьте ваши контакты, и {lawyer.user.get_full_name()} свяжется с вами',
                        'fields': ['name', 'phone', 'email']
                    }
                
                return JsonResponse(response_data)
                
            except Exception as ai_error:
                # Fallback response if AI fails
                fallback_message = f"""Спасибо за ваш вопрос! 

Для получения детальной консультации рекомендую обратиться к {lawyer.user.get_full_name()} напрямую:

📞 Телефон: {lawyer.phone}
📧 Email: {lawyer.user.email}
💰 Стоимость: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом

Хотите записаться на встречу?"""
                
                ChatMessage.objects.create(
                    session=session,
                    message_type='assistant',
                    content=fallback_message,
                    ai_model='fallback'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': fallback_message,
                    'should_collect_contact': True,
                    'contact_form': {
                        'title': 'Записаться на консультацию',
                        'subtitle': f'Оставьте ваши контакты, и {lawyer.user.get_full_name()} свяжется с вами',
                        'fields': ['name', 'phone', 'email']
                    }
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    def get_ai_response(self, system_prompt, user_message, session):
        """Get response from DeepSeek API"""
        start_time = datetime.now()
        
        headers = {
            'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Get conversation history for context
        recent_messages = ChatMessage.objects.filter(
            session=session
        ).order_by('-created_at')[:6]  # Last 6 messages for context
        
        messages = [{'role': 'system', 'content': system_prompt}]
        
        for msg in reversed(recent_messages):
            if msg.message_type == 'user':
                messages.append({'role': 'user', 'content': msg.content})
            elif msg.message_type == 'assistant' and msg.ai_model != 'system':
                messages.append({'role': 'assistant', 'content': msg.content})
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'max_tokens': 300,
            'temperature': 0.7,
            'stream': False
        }
        
        try:
            response = requests.post(
                settings.DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            end_time = datetime.now()
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'content': result['choices'][0]['message']['content'],
                'response_time': response_time,
                'tokens_used': result.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class SubmitContactAPIView(View):
    """Handle contact form submission and create lead"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            email = data.get('email', '').strip()
            
            if not all([session_id, name, phone]):
                return JsonResponse({'success': False, 'error': 'Name and phone are required'})
            
            # Get chat session
            session = get_object_or_404(ChatSession, session_id=session_id)
            lawyer = session.lawyer
            
            # Update session with contact info
            session.visitor_info.update({
                'name': name,
                'phone': phone,
                'email': email
            })
            session.consultation_requested = True
            session.save()
            
            # Create lead
            lead = Lead.objects.create(
                lawyer=lawyer,
                name=name,
                phone=phone,
                email=email,
                legal_category='Общая консультация',
                case_description=f'Запрос на консультацию через чат-бот. Сессия: {session_id}',
                source='website_chat',
                status='new',
                priority='medium',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            
            # Send confirmation message
            confirmation_message = f"""Отлично! Ваши контакты сохранены.

👤 Имя: {name}
📞 Телефон: {phone}
📧 Email: {email}

{lawyer.user.get_full_name()} свяжется с вами в ближайшее время для назначения встречи.

Обычно мы отвечаем в течение 1-2 часов в рабочее время (9:00-18:00).

Спасибо за обращение! 🙏"""
            
            ChatMessage.objects.create(
                session=session,
                message_type='assistant',
                content=confirmation_message,
                ai_model='system'
            )
            
            return JsonResponse({
                'success': True,
                'message': confirmation_message,
                'lead_created': True
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class GetChatHistoryAPIView(View):
    """Get chat history for a session"""
    
    def get(self, request):
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({'success': False, 'error': 'Session ID required'})
        
        try:
            session = get_object_or_404(ChatSession, session_id=session_id)
            messages = ChatMessage.objects.filter(session=session).order_by('created_at')
            
            message_data = []
            for msg in messages:
                message_data.append({
                    'type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'messages': message_data,
                'session_info': {
                    'lawyer_name': session.lawyer.user.get_full_name(),
                    'status': session.status
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400) 
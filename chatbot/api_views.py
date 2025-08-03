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
                visitor_name=visitor_name,
                visitor_ip=request.META.get('REMOTE_ADDR'),
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
            
            # Enhanced keyword detection for different types of requests
            explicit_appointment_keywords = ['записаться', 'встретиться', 'назначить встречу', 'прийти к вам', 'личная консультация', 'очная консультация']
            legal_keywords = ['закон', 'право', 'суд', 'договор', 'иск', 'развод', 'наследство', 'трудовой', 'административный', 'уголовный', 'гражданский', 'алименты', 'собственность', 'штраф', 'налог', 'регистрация', 'лицензия', 'аренда', 'купля', 'продажа']
            
            # Only consider explicit appointment requests, not general contact questions
            asking_for_appointment = any(keyword in user_message.lower() for keyword in explicit_appointment_keywords)
            asking_legal_question = any(keyword in user_message.lower() for keyword in legal_keywords)
            
            # Determine conversation context
            conversation_context = "general"
            if asking_for_appointment:
                conversation_context = "appointment"
            elif asking_legal_question:
                conversation_context = "legal_consultation"
            
            # Update session with legal category if detected
            if asking_legal_question and not session.legal_category:
                # Try to determine specific legal category
                if any(word in user_message.lower() for word in ['развод', 'алименты', 'брак', 'семья']):
                    session.legal_category = 'Семейное право'
                elif any(word in user_message.lower() for word in ['работа', 'трудовой', 'зарплата', 'увольнение']):
                    session.legal_category = 'Трудовое право'
                elif any(word in user_message.lower() for word in ['договор', 'сделка', 'покупка', 'продажа']):
                    session.legal_category = 'Гражданское право'
                elif any(word in user_message.lower() for word in ['штраф', 'административный', 'нарушение']):
                    session.legal_category = 'Административное право'
                elif any(word in user_message.lower() for word in ['наследство', 'завещание', 'наследник']):
                    session.legal_category = 'Наследственное право'
                else:
                    session.legal_category = 'Общая консультация'
                session.save()
            
            # Prepare enhanced system prompt for DeepSeek
            system_prompt = f"""Вы - профессиональный юридический консультант и помощник юриста {lawyer.user.get_full_name()} в Кыргызстане. Вы обладаете глубокими знаниями в области права КР и можете предоставлять квалифицированные консультации.

ИНФОРМАЦИЯ О ЮРИСТЕ:
- Имя: {lawyer.user.get_full_name()}
- Опыт работы: {lawyer.years_experience} лет
- Специализации: {', '.join(lawyer.specialties) if lawyer.specialties else 'Общая юридическая практика'}
- Контакты: {lawyer.user.email}
- Стоимость консультации: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом

ГЛАВНЫЙ ПРИНЦИП РАБОТЫ:
ВСЕГДА СНАЧАЛА ПРЕДОСТАВЛЯЙТЕ ПОЛЕЗНУЮ ЮРИДИЧЕСКУЮ ИНФОРМАЦИЮ И СОВЕТЫ, ОТВЕЧАЙТЕ НА ВОПРОС КЛИЕНТА МАКСИМАЛЬНО ПОДРОБНО И ТОЛЬКО ПОТОМ при необходимости предлагайте личную встречу.

ВАШИ ВОЗМОЖНОСТИ:
1. ОСНОВНАЯ ЗАДАЧА - ЮРИДИЧЕСКОЕ КОНСУЛЬТИРОВАНИЕ:
   - ОБЯЗАТЕЛЬНО объясняйте правовые нормы КР простым языком
   - ВСЕГДА анализируйте правовые ситуации и давайте конкретные рекомендации
   - ПОДРОБНО разъясняйте процедуры и требования законодательства
   - Помогайте с составлением документов (общие рекомендации с примерами)
   - Давайте детальные консультации по семейному, трудовому, гражданскому, административному праву

2. ПРАКТИЧЕСКАЯ ПОМОЩЬ:
   - ДЕТАЛЬНО объясняйте пошаговые действия для решения правовых вопросов
   - КОНКРЕТНО рассказывайте о необходимых документах и сроках
   - ОБЯЗАТЕЛЬНО предупреждайте о возможных рисках и последствиях
   - Давайте практические советы по взаимодействию с госорганами

3. ЗАПИСЬ НА КОНСУЛЬТАЦИЮ (ТОЛЬКО КОГДА ДЕЙСТВИТЕЛЬНО НЕОБХОДИМО):
   - Предлагайте личную встречу ТОЛЬКО в следующих случаях:
     * Нужен анализ большого количества документов
     * Сложное судебное дело требующее детального изучения
     * Клиент просит о встрече
     * Дело требует представительства в суде
   - НЕ спрашивайте контакты сразу - сначала дайте полную консультацию
   - Объясняйте конкретные преимущества очной консультации

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
- ВСЕГДА отвечайте профессионально, но доступным языком
- ОБЯЗАТЕЛЬНО давайте конкретные и практичные советы по вопросу
- Ссылайтесь на соответствующие статьи законов КР когда это уместно
- СНАЧАЛА максимально помогите онлайн, потом предлагайте встречу
- Всегда предупреждайте о важности соблюдения сроков
- Будьте максимально внимательны к деталям дела клиента

ОГРАНИЧЕНИЯ:
- Не давайте советы по уголовным делам без очной консультации
- При конфликте интересов направляйте к юристу
- Не гарантируйте 100% результат без изучения документов

ВАЖНО: Ваша цель - максимально помочь клиенту прямо сейчас, дать ему полезную информацию и конкретные советы. Встреча нужна только если онлайн-консультация недостаточна."""

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
                
                # Check if we need to collect contact info - only for explicit appointment requests
                # Also ensure we've had at least a couple exchanges before suggesting appointments
                message_count = ChatMessage.objects.filter(session=session, message_type='user').count()
                should_collect_contact = (asking_for_appointment and not session.visitor_phone) or (
                    message_count >= 3 and 'записаться' in ai_message.lower() and not session.visitor_phone
                )
                
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
                # Check if it's an API key issue
                if "API key not configured" in str(ai_error):
                    fallback_message = """🤖 **AI Консультант временно недоступен**

⚠️ Для работы AI-консультанта необходимо настроить API ключ DeepSeek.

**Как настроить:**
1. Получите API ключ на https://platform.deepseek.com/
2. Создайте файл .env в корне проекта
3. Добавьте строку: DEEPSEEK_API_KEY=ваш_ключ_здесь
4. Перезапустите сервер

**Пока что могу помочь с записью на консультацию к юристу.**"""
                else:
                    # Use simple rule-based fallback for common legal questions
                    fallback_message = self.get_simple_legal_response(user_message, lawyer)
                
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
        
        # Check if API key is configured
        if not settings.DEEPSEEK_API_KEY:
            raise Exception("DeepSeek API key not configured. Please set DEEPSEEK_API_KEY environment variable.")
        
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
                timeout=30  # Increased timeout
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
            print(f"DeepSeek API Error: {str(e)}")  # Debug logging
            print(f"Response status: {getattr(response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(response, 'text', 'N/A')[:500]}")
            raise Exception(f"DeepSeek API error: {str(e)}")
    
    def get_simple_legal_response(self, user_message, lawyer):
        """Simple rule-based responses for common legal questions when AI is unavailable"""
        message_lower = user_message.lower()
        
        # Contract/Agreement related
        if any(word in message_lower for word in ['договор', 'контракт', 'аренда', 'соглашение']):
            return f"""📄 **По вопросам договоров:**

**Основные требования к договорам в КР:**
• Договор должен быть составлен письменно
• Указаны все существенные условия
• Подписи сторон и дата
• Для аренды недвижимости - обязательная регистрация в Госрегистре

**Что нужно проверить:**
✅ Паспортные данные сторон
✅ Предмет договора (что именно арендуете/покупаете)
✅ Цена и сроки платежей
✅ Срок действия договора
✅ Ответственность сторон

⚠️ **Рекомендую**: Обязательно покажите договор юристу перед подписанием!

Хотите записаться на консультацию к {lawyer.user.get_full_name()}? Стоимость: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом"""

        # Divorce/Family law
        elif any(word in message_lower for word in ['развод', 'алименты', 'брак', 'семейн']):
            return f"""👨‍👩‍👧‍👦 **По семейным вопросам:**

**Процедура развода в КР:**
• Подача заявления в ЗАГС (при согласии) или суд
• Срок рассмотрения: 1 месяц в ЗАГСе, 2-6 месяцев в суде
• Госпошлина: от 500 до 2000 сом

**Алименты:**
• На ребенка: 25% от дохода на 1 ребенка, 33% на 2 детей
• Минимум: 30% от прожиточного минимума
• Взыскание через суд и судебных приставов

**Документы для развода:**
📋 Паспорта супругов
📋 Свидетельство о браке  
📋 Свидетельства о рождении детей
📋 справки о доходах (для алиментов)

Для детального разбора рекомендую консультацию с {lawyer.user.get_full_name()}."""

        # Labor law
        elif any(word in message_lower for word in ['работа', 'трудов', 'увольнение', 'зарплата']):
            return f"""💼 **По трудовым вопросам:**

**Ваши права работника:**
• Трудовой договор обязателен
• Оплата не реже 2 раз в месяц
• Отпуск 21 календарный день в году
• Больничные оплачиваются с первого дня

**При увольнении:**
• Предупреждение за 2 недели (при увольнении по желанию)
• Выплата всех зарплат и компенсаций
• Выдача трудовой книжки

**Нарушения работодателя:**
⚠️ Задержка зарплаты - штраф до 100,000 сом
⚠️ Незаконное увольнение - восстановление через суд
⚠️ Отказ в отпуске - жалоба в трудовую инспекцию

Нужна помощь? Запишитесь к {lawyer.user.get_full_name()}!"""

        # Real estate
        elif any(word in message_lower for word in ['недвижимость', 'квартира', 'дом', 'продажа', 'покупка']):
            return f"""🏠 **По вопросам недвижимости:**

**При покупке недвижимости проверьте:**
✅ Правоустанавливающие документы
✅ Выписку из Госреестра (не старше 30 дней)
✅ Справку об отсутствии долгов
✅ Согласие супруга продавца (если есть)
✅ Техпаспорт на квартиру

**Этапы сделки:**
1. Предварительный договор + задаток
2. Проверка документов юристом
3. Основной договор купли-продажи
4. Регистрация в Госрегистре
5. Передача ключей

**Госпошлины:**
• Регистрация права: 0.1% от стоимости (мин. 1000 сом)
• Нотариальное удостоверение: 0.5% от суммы

⚠️ Обязательно привлеките юриста для проверки документов!

Консультация {lawyer.user.get_full_name()}: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом"""

        # Default response
        else:
            return f"""Спасибо за ваш вопрос! 

🤖 AI-консультант временно недоступен (проблемы с сетью), но я могу помочь с базовой информацией.

**Популярные вопросы:**
• Договоры и контракты
• Семейное право (развод, алименты)
• Трудовые споры
• Недвижимость

Для подробной консультации рекомендую обратиться к {lawyer.user.get_full_name()}:

📧 Email: {lawyer.user.email}
💰 Стоимость: {lawyer.consultation_fee if lawyer.consultation_fee > 0 else 'Первая консультация бесплатно'} сом

Хотите записаться на встречу?"""


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
            session.visitor_name = name
            session.visitor_phone = phone
            session.visitor_email = email
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


@method_decorator(csrf_exempt, name='dispatch')
class ScheduleAppointmentAPIView(View):
    """Handle appointment scheduling from chat"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            appointment_time = data.get('appointment_time')
            appointment_date = data.get('appointment_date')
            consultation_type = data.get('consultation_type', 'general')
            
            if not all([session_id, appointment_time, appointment_date]):
                return JsonResponse({'success': False, 'error': 'Session ID, time and date are required'})
            
            # Get chat session
            session = get_object_or_404(ChatSession, session_id=session_id)
            lawyer = session.lawyer
            
            # Import here to avoid circular imports
            from leads.models import Consultation
            from datetime import datetime
            
            # Parse appointment datetime
            appointment_datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date/time format'})
            
            # Create or get lead from session
            if session.visitor_phone and session.visitor_name:
                # Try to find existing lead or create new one
                from leads.models import Lead
                lead, created = Lead.objects.get_or_create(
                    lawyer=lawyer,
                    phone=session.visitor_phone,
                    defaults={
                        'name': session.visitor_name,
                        'email': session.visitor_email or '',
                        'legal_category': session.legal_category or 'Общая консультация',
                        'case_description': f'Консультация через чат-бот. Сессия: {session_id}',
                        'source': 'website_chat',
                        'status': 'new',
                        'priority': 'medium',
                        'ip_address': request.META.get('REMOTE_ADDR', ''),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'referrer': request.META.get('HTTP_REFERER', '')
                    }
                )
                
                # Create consultation appointment
                consultation = Consultation.objects.create(
                    lawyer=lawyer,
                    lead=lead,
                    scheduled_time=appointment_datetime,
                    duration_minutes=60,  # Default 1 hour
                    consultation_type=consultation_type,
                    meeting_method='in_person',  # Default
                    status='scheduled',
                    agenda=f'Консультация по вопросу: {session.legal_category or "Общие правовые вопросы"}',
                    notes=f'Запись через чат-бот. Сессия: {session_id}'
                )
                
                # Update session
                session.consultation_requested = True
                session.save()
                
                # Send confirmation message
                confirmation_message = f"""✅ Отлично! Консультация успешно назначена.

📅 Дата: {appointment_datetime.strftime('%d.%m.%Y')}
🕐 Время: {appointment_datetime.strftime('%H:%M')}
👤 Клиент: {session.visitor_name}
📞 Телефон: {session.visitor_phone}
📧 Email: {session.visitor_email or 'Не указан'}
⚖️ Тема: {session.legal_category or 'Общая консультация'}

{lawyer.user.get_full_name()} свяжется с вами за день до встречи для подтверждения.

Консультация будет проходить в офисе юриста. Адрес и дополнительную информацию вы получите при подтверждении.

До встречи! 🤝"""
                
                ChatMessage.objects.create(
                    session=session,
                    message_type='assistant',
                    content=confirmation_message,
                    ai_model='system'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': confirmation_message,
                    'appointment_id': consultation.id,
                    'appointment_details': {
                        'date': appointment_datetime.strftime('%d.%m.%Y'),
                        'time': appointment_datetime.strftime('%H:%M'),
                        'lawyer': lawyer.user.get_full_name(),
                        'client': session.visitor_name,
                        'phone': session.visitor_phone,
                        'category': session.legal_category
                    }
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Contact information required. Please provide name and phone number first.'
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
                    'status': session.status,
                    'visitor_name': session.visitor_name,
                    'visitor_phone': session.visitor_phone,
                    'legal_category': session.legal_category
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400) 
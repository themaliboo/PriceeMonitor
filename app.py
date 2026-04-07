from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_file
from functools import wraps
from datetime import datetime
from database import Database
from parser import CompetitorParser
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
# ========== ИНИЦИАЛИЗАЦИЯ ==========
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

db = Database()
parser = CompetitorParser()

# ========== НАСТРОЙКИ ПОЧТЫ MAIL.RU ==========
# ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ:
SMTP_HOST = "smtp.mail.ru"
SMTP_PORT = 587
SMTP_USER = "pricemonitor11@mail.ru"  # ВАШ EMAIL
SMTP_PASSWORD = "awBm0vm6PpkVTLjTQUcr"  # ПАРОЛЬ ПРИЛОЖЕНИЯ


def send_verification_email(to_email, code):
    subject = "Подтверждение регистрации - PriceMonitor"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Добро пожаловать в PriceMonitor!</h2>
        <p>Ваш код подтверждения: <strong style="font-size: 24px; color: #667eea;">{code}</strong></p>
        <p>Введите этот код на сайте для завершения регистрации.</p>
        <p>Код действителен 24 часа.</p>
        <hr>
        <p>С уважением,<br>Команда PriceMonitor</p>
    </body>
    </html>
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Письмо отправлено на {to_email}")
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False


@app.route('/demo')
def demo():
    """Демонстрационная страница с примером работы"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Демо - PriceMonitor</title>
        <meta charset="UTF-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: transparent;
                color: #e0e0e0; 
                padding: 40px;
                min-height: 100vh;
            }
            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #0a0a0e;
                z-index: -2;
            }
            body::after {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 20% 50%, rgba(30,30,60,0.4) 0%, transparent 60%),
                            radial-gradient(circle at 80% 80%, rgba(60,40,80,0.3) 0%, transparent 60%);
                z-index: -1;
            }
            .container { max-width: 1000px; margin: 0 auto; }
            .card { background: rgba(20,20,26,0.7); backdrop-filter: blur(10px); border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid rgba(42,42,53,0.5); }
            h1 { margin-bottom: 20px; color: #fff; text-align: center; font-weight: 500; letter-spacing: -0.5px; }
            h2 { margin-bottom: 20px; color: #fff; font-size: 18px; font-weight: 500; }
            .btn { display: inline-block; padding: 10px 20px; background: rgba(42,42,53,0.9); color: #fff; text-decoration: none; border-radius: 6px; margin-right: 10px; transition: all 0.2s; font-size: 14px; border: 1px solid rgba(58,58,72,0.5); }
            .btn-back { background: rgba(26,26,36,0.9); border: 1px solid rgba(42,42,53,0.5); }
            .btn:hover { background: rgba(58,58,72,0.9); transform: translateY(-1px); }
            .demo-item { 
                display: flex; 
                align-items: center; 
                gap: 20px; 
                padding: 20px; 
                background: rgba(26,26,36,0.6); 
                border-radius: 12px; 
                margin-bottom: 16px; 
                border: 1px solid rgba(42,42,53,0.5);
                transition: all 0.3s;
            }
            .demo-item:hover { transform: translateX(5px); border-color: rgba(74,74,96,0.8); background: rgba(30,30,42,0.7); }
            .demo-image {
                width: 80px;
                height: 80px;
                border-radius: 10px;
                background-size: cover;
                background-position: center;
                flex-shrink: 0;
            }
            .demo-content { flex: 1; }
            .demo-title { font-weight: 500; font-size: 16px; margin-bottom: 4px; color: #e0e0e0; }
            .demo-price { font-size: 22px; color: #8cd4a0; font-weight: 500; }
            .demo-old-price { font-size: 13px; color: #a0a0a0; text-decoration: line-through; margin-top: 2px; }
            .badge { display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 11px; margin-bottom: 8px; font-weight: 500; }
            .avito-badge { background: rgba(42,58,74,0.8); color: #80c0f0; }
            .ozon-badge { background: rgba(58,42,42,0.8); color: #f0a0a0; }
            .wb-badge { background: rgba(42,42,74,0.8); color: #a0a0f0; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
            .footer { text-align: center; margin-top: 30px; color: #6a6a7a; font-size: 12px; }
            .features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px; }
            .feature-card { background: rgba(26,26,36,0.6); padding: 28px 20px; border-radius: 12px; text-align: center; border: 1px solid rgba(42,42,53,0.5); transition: all 0.3s; }
            .feature-card:hover { transform: translateY(-4px); border-color: rgba(74,74,96,0.8); background: rgba(30,30,42,0.7); }
            .feature-icon { width: 48px; height: 48px; margin: 0 auto 16px; background-size: contain; background-repeat: no-repeat; background-position: center; opacity: 0.9; }
            .price-icon { background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%238cd4a0"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.31-8.86c-1.69-.23-2.03-.78-2.03-1.37 0-.72.66-1.27 1.8-1.27 1.13 0 1.78.55 1.84 1.11h1.69c-.07-1.26-1.07-2.27-2.54-2.44V6h-1.9v1.33c-1.33.23-2.33 1.13-2.33 2.33 0 1.5 1.08 2.33 2.96 2.67 1.7.29 2.03.86 2.03 1.47 0 .79-.75 1.33-1.95 1.33-1.21 0-1.95-.54-2.02-1.23h-1.69c.08 1.44 1.13 2.44 2.71 2.63V18h1.9v-1.37c1.39-.24 2.44-1.19 2.44-2.53 0-1.61-1.14-2.53-3.03-2.86z"/></svg>'); }
            .chart-icon { background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%238cd4a0"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>'); }
            .telegram-icon { background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%238cd4a0"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/><path d="M12 8v4l3 3-3-3V8z"/></svg>'); }
            .feature-title { font-size: 16px; font-weight: 500; margin-bottom: 8px; color: #e0e0e0; }
            .feature-desc { font-size: 13px; color: #8a8a9a; line-height: 1.4; }
            @media (max-width: 768px) { .features-grid { grid-template-columns: 1fr; } .demo-item { flex-direction: column; text-align: center; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Демо-режим</h1>
                <a href="/" class="btn btn-back">← На главную</a>
            </div>

            <div class="card">
                <h2>Мониторинг цен конкурентов</h2>
                <p style="margin-bottom: 20px; color: #8a8a9a; font-size: 14px;">Реальные данные с маркетплейсов</p>

                <div class="demo-item">
                    <div class="demo-image" style="background-image: url('https://www.apple.com/newsroom/images/product/iphone/standard/iPhone_15_Pro_hero_091223.jpg'); background-size: cover;"></div>
                    <div class="demo-content">
                        <div><span class="badge avito-badge">Avito</span></div>
                        <div class="demo-title">iPhone 15 Pro 128GB</div>
                        <div class="demo-price">89 990 ₽</div>
                        <div class="demo-old-price">Было: 94 990 ₽</div>
                    </div>
                </div>

                <div class="demo-item">
                    <div class="demo-image" style="background-image: url('https://image-us.samsung.com/SamsungUS/home/mobile/phones/galaxy-s24-ultra/S24_Ultra_Graphite_Hero_240131.jpg'); background-size: cover;"></div>
                    <div class="demo-content">
                        <div><span class="badge ozon-badge">Ozon</span></div>
                        <div class="demo-title">Samsung Galaxy S24 Ultra</div>
                        <div class="demo-price">112 490 ₽</div>
                        <div class="demo-old-price">Было: 109 990 ₽</div>
                    </div>
                </div>

                <div class="demo-item">
                    <div class="demo-image" style="background-image: url('https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-pro-2-hero?wid=940&hei=940&fmt=jpeg&qlt=90&.v=1661209562052'); background-size: cover;"></div>
                    <div class="demo-content">
                        <div><span class="badge wb-badge">Wildberries</span></div>
                        <div class="demo-title">Apple AirPods Pro 2</div>
                        <div class="demo-price">24 990 ₽</div>
                        <div class="demo-old-price">Было: 27 990 ₽</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Возможности сервиса</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon price-icon"></div>
                        <div class="feature-title">Актуальные цены</div>
                        <div class="feature-desc">Мониторинг цен на Avito, Ozon и Wildberries</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon chart-icon"></div>
                        <div class="feature-title">Аналитика и графики</div>
                        <div class="feature-desc">История изменений цен и тренды</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon telegram-icon"></div>
                        <div class="feature-title">Telegram уведомления</div>
                        <div class="feature-desc">Мгновенные оповещения об изменениях</div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>PriceMonitor — профессиональный инструмент для анализа цен</p>
            </div>
        </div>
    </body>
    </html>
    '''

# ========== ГЛАВНАЯ СТРАНИЦА С ДИНАМИЧЕСКИМ ФОНОМ ==========
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PriceMonitor - Мониторинг цен конкурентов</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0e; color: #e0e0e0; overflow-x: hidden; }

        .dynamic-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -2; overflow: hidden; }
        .particle { position: absolute; background: linear-gradient(135deg, rgba(100,100,150,0.4), rgba(80,80,120,0.2)); border-radius: 50%; animation: float 20s infinite linear; pointer-events: none; }
        @keyframes float { 0% { transform: translateY(100vh) rotate(0deg); opacity: 0; } 10% { opacity: 0.6; } 90% { opacity: 0.6; } 100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; } }

        .gradient-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 20% 50%, rgba(30,30,60,0.4) 0%, transparent 60%), radial-gradient(circle at 80% 80%, rgba(60,40,80,0.3) 0%, transparent 60%); z-index: -1; }

        /* Шапка на всю ширину */
        .header {
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            background: rgba(10,10,14,0.5);
            position: sticky;
            top: 0;
            width: 100%;
            z-index: 100;
        }
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            position: relative;
            z-index: 1;
        }
        .logo { font-size: 24px; font-weight: 600; background: linear-gradient(135deg, #ffffff, #a0a0c0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .logo a { text-decoration: none; background: linear-gradient(135deg, #ffffff, #a0a0c0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav a { color: #a0a0b0; text-decoration: none; margin-left: 28px; font-size: 14px; transition: color 0.2s; cursor: pointer; }
        .nav a:hover { color: #ffffff; }

        .hero { text-align: center; padding: 100px 0 80px; }
        .hero h1 { font-size: 56px; font-weight: 700; margin-bottom: 24px; background: linear-gradient(135deg, #ffffff 0%, #9090b0 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .hero p { font-size: 18px; color: #a0a0b0; max-width: 600px; margin: 0 auto 32px; }
        .hero-buttons { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }

        .btn { display: inline-block; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px; transition: all 0.2s; cursor: pointer; }
        .btn-primary { background: rgba(42,42,53,0.9); backdrop-filter: blur(5px); color: #ffffff; border: 1px solid rgba(58,58,72,0.5); }
        .btn-primary:hover { background: rgba(58,58,72,0.9); transform: translateY(-2px); }
        .btn-outline { background: transparent; color: #a0a0b0; border: 1px solid rgba(42,42,53,0.8); }
        .btn-outline:hover { border-color: rgba(74,74,96,0.8); color: #ffffff; transform: translateY(-2px); }

        .features { padding: 80px 0; border-top: 1px solid rgba(255,255,255,0.05); }
        .features h2 { text-align: center; font-size: 32px; font-weight: 600; margin-bottom: 56px; background: linear-gradient(135deg, #ffffff, #9090b0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .features-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; }
        .feature { text-align: center; padding: 32px 24px; background: rgba(20,20,26,0.6); backdrop-filter: blur(5px); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); transition: transform 0.3s, border-color 0.3s; }
        .feature:hover { transform: translateY(-5px); border-color: rgba(100,100,150,0.3); }
        .feature-icon { font-size: 40px; margin-bottom: 16px; }
        .feature h3 { font-size: 18px; margin-bottom: 8px; font-weight: 600; color: #ffffff; }
        .feature p { font-size: 14px; color: #8a8a9a; }

        .pricing { padding: 8INDEX_TEMPLATE = '''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PriceMonitor - Мониторинг цен конкурентов</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0e; color: #e0e0e0; overflow-x: hidden; }

        .dynamic-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -2; overflow: hidden; }
        .particle { position: absolute; background: linear-gradient(135deg, rgba(100,100,150,0.4), rgba(80,80,120,0.2)); border-radius: 50%; animation: float 20s infinite linear; pointer-events: none; }
        @keyframes float { 0% { transform: translateY(100vh) rotate(0deg); opacity: 0; } 10% { opacity: 0.6; } 90% { opacity: 0.6; } 100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; } }

        .gradient-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 20% 50%, rgba(30,30,60,0.4) 0%, transparent 60%), radial-gradient(circle at 80% 80%, rgba(60,40,80,0.3) 0%, transparent 60%); z-index: -1; }

        .header {
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            background: rgba(10,10,14,0.5);
            position: sticky;
            top: 0;
            width: 100%;
            z-index: 100;
        }
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            position: relative;
            z-index: 1;
        }
        .logo { font-size: 24px; font-weight: 600; background: linear-gradient(135deg, #ffffff, #a0a0c0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .logo a { text-decoration: none; background: linear-gradient(135deg, #ffffff, #a0a0c0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav a { color: #a0a0b0; text-decoration: none; margin-left: 28px; font-size: 14px; transition: color 0.2s; cursor: pointer; }
        .nav a:hover { color: #ffffff; }

        .hero { text-align: center; padding: 100px 0 80px; }
        .hero h1 { font-size: 56px; font-weight: 700; margin-bottom: 24px; background: linear-gradient(135deg, #ffffff 0%, #9090b0 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .hero p { font-size: 18px; color: #a0a0b0; max-width: 600px; margin: 0 auto 32px; }
        .hero-buttons { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }

        .btn { display: inline-block; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px; transition: all 0.2s; cursor: pointer; }
        .btn-primary { background: rgba(42,42,53,0.9); backdrop-filter: blur(5px); color: #ffffff; border: 1px solid rgba(58,58,72,0.5); }
        .btn-primary:hover { background: rgba(58,58,72,0.9); transform: translateY(-2px); }
        .btn-outline { background: transparent; color: #a0a0b0; border: 1px solid rgba(42,42,53,0.8); }
        .btn-outline:hover { border-color: rgba(74,74,96,0.8); color: #ffffff; transform: translateY(-2px); }

        /* Возможности сервиса - не выделяются */
        .features { padding: 80px 0; border-top: 1px solid rgba(255,255,255,0.05); }
        .features h2 { text-align: center; font-size: 32px; font-weight: 600; margin-bottom: 56px; background: linear-gradient(135deg, #ffffff, #9090b0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .features-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; }
        .feature {
            text-align: center;
            padding: 32px 24px;
            background: rgba(20,20,26,0.6);
            backdrop-filter: blur(5px);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.05);
            transition: transform 0.3s, border-color 0.3s;
            cursor: pointer;
            user-select: none;
        }
        .feature:hover {
            transform: translateY(-5px);
            border-color: rgba(100,100,150,0.3);
        }
        .feature-icon {
            font-size: 40px;
            margin-bottom: 16px;
            pointer-events: none;
        }
        .feature h3 {
            font-size: 18px;
            margin-bottom: 8px;
            font-weight: 600;
            color: #ffffff;
            pointer-events: none;
        }
        .feature p {
            font-size: 14px;
            color: #8a8a9a;
            pointer-events: none;
        }

        /* Тарифы - не выделяются */
        .pricing { padding: 80px 0; border-top: 1px solid rgba(255,255,255,0.05); background: rgba(15,15,18,0.5); backdrop-filter: blur(5px); }
        .pricing h2 { text-align: center; font-size: 32px; font-weight: 600; margin-bottom: 56px; background: linear-gradient(135deg, #ffffff, #9090b0); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .pricing-grid { display: flex; justify-content: center; gap: 32px; flex-wrap: wrap; }
        .pricing-card {
            background: rgba(20,20,26,0.8);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(42,42,53,0.5);
            border-radius: 20px;
            padding: 32px;
            width: 280px;
            text-align: center;
            transition: transform 0.3s, border-color 0.3s;
            cursor: pointer;
            user-select: none;
        }
        .pricing-card:hover {
            transform: translateY(-4px);
            border-color: rgba(100,100,150,0.4);
        }
        .pricing-card h3 {
            font-size: 22px;
            margin-bottom: 16px;
            color: #ffffff;
            pointer-events: none;
        }
        .pricing-price {
            font-size: 42px;
            font-weight: 700;
            color: #ffffff;
            margin: 20px 0;
            pointer-events: none;
        }
        .pricing-features {
            list-style: none;
            margin: 20px 0;
            font-size: 13px;
            color: #a0a0b0;
            pointer-events: none;
        }
        .pricing-features li {
            padding: 8px 0;
            pointer-events: none;
        }
        .pricing-card .btn {
            pointer-events: auto;
        }

        .footer { padding: 40px 0; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; font-size: 12px; color: #6a6a7a; }

        /* Модальные окна */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(8px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.4s ease;
            cursor: pointer;
        }
        .modal.show {
            display: flex;
            opacity: 1;
        }
        .modal-content {
            cursor: default;
            background: rgba(20,20,26,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            width: 520px;
            max-width: 90%;
            padding: 32px;
            border: 1px solid rgba(255,255,255,0.1);
            transform: translateY(20px) scale(0.95);
            transition: transform 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            position: relative;
        }
        .modal-content h2 { margin-bottom: 24px; text-align: center; color: #fff; }
        .modal-content input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(15,15,18,0.8);
            border: 1px solid #2a2a35;
            border-radius: 8px;
            color: #fff;
            box-sizing: border-box;
            transition: border 0.2s;
        }
        .modal-content input:focus { outline: none; border-color: #667eea; }
        .modal-content button {
            width: 100%;
            padding: 12px;
            background: #2a2a35;
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
            transition: background 0.2s;
        }
        .modal-content button:hover { background: #3a3a48; }
        .modal-content a {
            color: #a0a0b0;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 16px;
            font-size: 13px;
            cursor: pointer;
            transition: color 0.2s;
        }
        .modal-content a:hover { color: #fff; }
        .close-modal {
            position: absolute;
            top: 16px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #a0a0b0;
            transition: color 0.2s;
        }
        .close-modal:hover { color: #fff; }

        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(20,20,26,0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 16px 24px;
            min-width: 280px;
            border-left: 4px solid;
            z-index: 1100;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        }
        .toast.show { transform: translateX(0); }
        .toast.error { border-left-color: #f56565; }
        .toast.success { border-left-color: #8cd4a0; }
        .toast.warning { border-left-color: #ecc94b; }
        .toast-content { display: flex; justify-content: space-between; align-items: center; }
        .toast-message { color: #fff; font-size: 14px; }
        .toast-close { cursor: pointer; color: #a0a0b0; font-size: 20px; margin-left: 15px; transition: color 0.2s; }
        .toast-close:hover { color: #fff; }

        .demo-features {
            display: flex;
            justify-content: space-around;
            gap: 16px;
            margin: 20px 0;
        }
        .demo-feature {
            flex: 1;
            text-align: center;
            padding: 16px;
            background: rgba(26,26,36,0.5);
            border-radius: 12px;
            transition: all 0.3s ease;
            cursor: pointer;
            user-select: none;
        }
        .demo-feature:hover {
            transform: translateY(-5px);
            background: rgba(30,30,42,0.7);
        }
        .demo-feature-icon {
            margin-bottom: 8px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .demo-feature-title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            color: #e0e0e0;
        }
        .demo-feature-desc {
            font-size: 11px;
            color: #a0a0b0;
        }

        .demo-products {
            margin: 16px 0;
        }
        .demo-product-card {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px;
            background: rgba(26,26,36,0.6);
            border-radius: 12px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
            cursor: pointer;
            user-select: none;
            border: 1px solid rgba(42,42,53,0.3);
        }
        .demo-product-card:hover {
            transform: translateX(5px);
            background: rgba(30,30,42,0.8);
            border-color: rgba(74,74,96,0.6);
        }
        .demo-product-image {
            width: 55px;
            height: 55px;
            background-size: cover;
            background-position: center;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }
        .demo-product-card:hover .demo-product-image {
            transform: scale(1.05);
        }
        .demo-product-info {
            flex: 1;
        }
        .demo-product-title {
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 5px;
            color: #e0e0e0;
        }
        .demo-product-price {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 4px;
        }
        .current-price {
            color: #8cd4a0;
            font-weight: 600;
            font-size: 16px;
        }
        .old-price {
            color: #a0a0a0;
            text-decoration: line-through;
            font-size: 13px;
        }
        .demo-product-change {
            font-size: 11px;
            color: #8cd4a0;
        }

        @media (max-width: 768px) {
            .hero h1 { font-size: 36px; }
            .hero p { font-size: 16px; }
            .features-grid { grid-template-columns: 1fr; }
            .nav a { margin-left: 16px; }
            .demo-features { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="dynamic-bg" id="particles"></div>
    <div class="gradient-overlay"></div>

    <div class="header">
        <div class="header-content">
            <div class="logo"><a href="/">PriceMonitor</a></div>
            <div class="nav">
                <a href="/">Главная</a>
                <a onclick="openDemoModal()">Демо</a>
                <a onclick="openLoginModal()">Вход</a>
                <a onclick="openRegisterModal()">Регистрация</a>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1>Мониторинг цен конкурентов</h1>
            <p>Отслеживайте цены на Wildberries, Ozon и Avito. Получайте AI-рекомендации и увеличивайте прибыль.</p>
            <div class="hero-buttons">
                <a onclick="openDemoModal()" class="btn btn-primary">Посмотреть демо</a>
                <a onclick="openRegisterModal()" class="btn btn-outline">Начать бесплатно</a>
            </div>
        </div>

        <div class="features">
            <h2>Возможности сервиса</h2>
            <div class="features-grid">
                <div class="feature" onclick="openRegisterModal()">
                    <div class="feature-icon">◈</div>
                    <h3>Мониторинг 24/7</h3>
                    <p>Автоматическое отслеживание цен конкурентов в реальном времени</p>
                </div>
                <div class="feature" onclick="openRegisterModal()">
                    <div class="feature-icon">◇</div>
                    <h3>AI рекомендации</h3>
                    <p>Умные советы по оптимальной цене на основе анализа рынка</p>
                </div>
                <div class="feature" onclick="openRegisterModal()">
                    <div class="feature-icon">◎</div>
                    <h3>Telegram бот</h3>
                    <p>Мгновенные уведомления об изменении цен конкурентов</p>
                </div>
                <div class="feature" onclick="openRegisterModal()">
                    <div class="feature-icon">○</div>
                    <h3>Детальная аналитика</h3>
                    <p>Графики и отчёты для принятия решений</p>
                </div>
            </div>
        </div>

        <div class="pricing">
            <h2>Тарифы</h2>
            <div class="pricing-grid">
                <div class="pricing-card" onclick="openRegisterModal()">
                    <h3>Бесплатный</h3>
                    <div class="pricing-price">0 ₽</div>
                    <ul class="pricing-features">
                        <li>1 тестовый запрос</li>
                        <li>Базовая аналитика</li>
                    </ul>
                    <a onclick="event.stopPropagation(); openRegisterModal()" class="btn btn-outline">Начать</a>
                </div>
                <div class="pricing-card" onclick="openRegisterModal()">
                    <h3>Месячный</h3>
                    <div class="pricing-price">1 990 ₽</div>
                    <ul class="pricing-features">
                        <li>Неограниченные запросы</li>
                        <li>Автопарсинг</li>
                        <li>Telegram уведомления</li>
                    </ul>
                    <a onclick="event.stopPropagation(); openRegisterModal()" class="btn btn-primary">Выбрать</a>
                </div>
                <div class="pricing-card" onclick="openRegisterModal()">
                    <h3>Годовой</h3>
                    <div class="pricing-price">14 990 ₽</div>
                    <ul class="pricing-features">
                        <li>Экономия 30%</li>
                        <li>Все функции</li>
                        <li>Приоритетная поддержка</li>
                    </ul>
                    <a onclick="event.stopPropagation(); openRegisterModal()" class="btn btn-primary">Выбрать</a>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>PriceMonitor — инструмент для анализа цен конкурентов</p>
        </div>
    </div>

    <!-- Модальные окна -->
    <div id="loginModal" class="modal">
        <div class="modal-content" style="width: 400px;">
            <span class="close-modal" onclick="closeLoginModal()">&times;</span>
            <h2>Вход в аккаунт</h2>
            <form id="loginForm">
                <input type="email" id="loginEmail" placeholder="Email" required>
                <input type="password" id="loginPassword" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
            <a onclick="closeLoginModal(); openRegisterModal()">Нет аккаунта? Зарегистрироваться</a>
            <a onclick="closeLoginModal(); openForgotModal()">Забыли пароль?</a>
        </div>
    </div>

    <div id="registerModal" class="modal">
        <div class="modal-content" style="width: 400px;">
            <span class="close-modal" onclick="closeRegisterModal()">&times;</span>
            <h2>Регистрация</h2>
            <form id="registerForm">
                <input type="text" id="regName" placeholder="Имя">
                <input type="email" id="regEmail" placeholder="Email" required>
                <input type="tel" id="regPhone" placeholder="Телефон">
                <input type="password" id="regPassword" placeholder="Пароль" required>
                <input type="password" id="regConfirm" placeholder="Подтвердите пароль" required>
                <button type="submit">Зарегистрироваться</button>
            </form>
            <a onclick="closeRegisterModal(); openLoginModal()">Уже есть аккаунт? Войти</a>
        </div>
    </div>

    <div id="forgotModal" class="modal">
        <div class="modal-content" style="width: 400px;">
            <span class="close-modal" onclick="closeForgotModal()">&times;</span>
            <h2>Восстановление пароля</h2>
            <form id="forgotForm">
                <input type="email" id="forgotEmail" placeholder="Email" required>
                <button type="submit">Отправить код</button>
            </form>
            <a onclick="closeForgotModal(); openLoginModal()">Вернуться ко входу</a>
        </div>
    </div>

    <div id="resetCodeModal" class="modal">
        <div class="modal-content" style="width: 400px;">
            <span class="close-modal" onclick="closeResetCodeModal()">&times;</span>
            <h2>Введите код</h2>
            <p style="color:#a0a0b0; text-align:center; margin-bottom:15px">Код отправлен на email</p>
            <form id="resetCodeForm">
                <input type="text" id="resetCode" placeholder="Код из письма" maxlength="6">
                <input type="password" id="newPassword" placeholder="Новый пароль">
                <input type="password" id="confirmNewPassword" placeholder="Подтвердите пароль">
                <button type="submit">Сбросить пароль</button>
            </form>
        </div>
    </div>

    <div id="demoModal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeDemoModal()">&times;</span>
            <h2>Демо-режим</h2>

            <div class="demo-features">
                <div class="demo-feature" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-feature-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8cd4a0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 6v6l4 2"/>
                        </svg>
                    </div>
                    <div class="demo-feature-title">Реальные цены</div>
                    <div class="demo-feature-desc">Avito, Ozon, WB</div>
                </div>
                <div class="demo-feature" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-feature-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8cd4a0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 3v18h18"/>
                            <path d="M18 17V9"/>
                            <path d="M12 17V5"/>
                            <path d="M6 17v-3"/>
                        </svg>
                    </div>
                    <div class="demo-feature-title">История изменений</div>
                    <div class="demo-feature-desc">Графики и тренды</div>
                </div>
                <div class="demo-feature" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-feature-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8cd4a0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2a10 10 0 0 1 10 10c0 5-3 9-10 9-4 0-7-2-9-5"/>
                            <path d="M12 8v4l3 3"/>
                            <path d="M5 3v4h4"/>
                        </svg>
                    </div>
                    <div class="demo-feature-title">AI рекомендации</div>
                    <div class="demo-feature-desc">Оптимальная цена</div>
                </div>
            </div>

            <div class="demo-products">
                <div class="demo-product-card" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-product-image" style="background-image: url('https://www.apple.com/newsroom/images/product/iphone/standard/iPhone_15_Pro_hero_091223.jpg');"></div>
                    <div class="demo-product-info">
                        <div class="demo-product-title">iPhone 15 Pro</div>
                        <div class="demo-product-price">
                            <span class="current-price">89 990 ₽</span>
                            <span class="old-price">94 990 ₽</span>
                        </div>
                        <div class="demo-product-change">Снижение на 5 000 ₽</div>
                    </div>
                </div>
                <div class="demo-product-card" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-product-image" style="background-image: url('https://image-us.samsung.com/SamsungUS/home/mobile/phones/galaxy-s24-ultra/S24_Ultra_Graphite_Hero_240131.jpg');"></div>
                    <div class="demo-product-info">
                        <div class="demo-product-title">Samsung S24 Ultra</div>
                        <div class="demo-product-price">
                            <span class="current-price">112 490 ₽</span>
                            <span class="old-price">109 990 ₽</span>
                        </div>
                        <div class="demo-product-change">Повышение на 2 500 ₽</div>
                    </div>
                </div>
                <div class="demo-product-card" onclick="openRegisterModal(); closeDemoModal();">
                    <div class="demo-product-image" style="background-image: url('https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-pro-2-hero?wid=940&hei=940&fmt=jpeg&qlt=90&.v=1661209562052');"></div>
                    <div class="demo-product-info">
                        <div class="demo-product-title">AirPods Pro 2</div>
                        <div class="demo-product-price">
                            <span class="current-price">24 990 ₽</span>
                            <span class="old-price">27 990 ₽</span>
                        </div>
                        <div class="demo-product-change">Снижение на 3 000 ₽</div>
                    </div>
                </div>
            </div>

            <button onclick="closeDemoModal(); openRegisterModal()" class="btn btn-primary" style="width:100%">Начать отслеживать</button>
        </div>
    </div>

    <div id="toastContainer"></div>

    <script>
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 60; i++) {
                const p = document.createElement('div');
                p.classList.add('particle');
                p.style.width = (Math.random() * 6 + 2) + 'px';
                p.style.height = p.style.width;
                p.style.left = Math.random() * 100 + '%';
                p.style.animationDuration = (Math.random() * 25 + 15) + 's';
                p.style.animationDelay = (Math.random() * 20) + 's';
                p.style.opacity = Math.random() * 0.4 + 0.1;
                container.appendChild(p);
            }
        }
        createParticles();

        function showToast(message, type = 'error') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<div class="toast-content"><span class="toast-message">${message}</span><span class="toast-close" onclick="this.parentElement.parentElement.remove()">×</span></div>`;
            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function openModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('show'), 10);
        }

        function closeModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.classList.remove('show');
            setTimeout(() => modal.style.display = 'none', 400);
        }

        function setupModalCloseOnBackground() {
            const modals = ['loginModal', 'registerModal', 'forgotModal', 'resetCodeModal', 'demoModal'];
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.addEventListener('click', function(e) {
                        if (e.target === modal) {
                            closeModal(modalId);
                        }
                    });
                }
            });
        }

        function openLoginModal() { openModal('loginModal'); }
        function closeLoginModal() { closeModal('loginModal'); }
        function openRegisterModal() { openModal('registerModal'); }
        function closeRegisterModal() { closeModal('registerModal'); }
        function openForgotModal() { openModal('forgotModal'); }
        function closeForgotModal() { closeModal('forgotModal'); }
        function openResetCodeModal() { openModal('resetCodeModal'); }
        function closeResetCodeModal() { closeModal('resetCodeModal'); }
        function openDemoModal() { openModal('demoModal'); }
        function closeDemoModal() { closeModal('demoModal'); }

        document.addEventListener('DOMContentLoaded', setupModalCloseOnBackground);

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Вход выполнен! Перенаправление...', 'success');
                    setTimeout(() => window.location.href = '/dashboard', 1000);
                } else {
                    showToast(data.error, 'error');
                }
            } catch(e) { showToast('Ошибка подключения', 'error'); }
        });

        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const phone = document.getElementById('regPhone').value;
            const password = document.getElementById('regPassword').value;
            const confirm = document.getElementById('regConfirm').value;
            if (password !== confirm) { showToast('Пароли не совпадают', 'error'); return; }
            if (password.length < 6) { showToast('Пароль минимум 6 символов', 'error'); return; }
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, phone, password })
            });
            const data = await res.json();
            if (data.success) {
                showToast('Регистрация успешна! Проверьте почту для подтверждения', 'success');
                setTimeout(() => window.location.href = '/', 2000);
            } else {
                showToast(data.error, 'error');
            }
        });

        document.getElementById('forgotForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('forgotEmail').value;
            const res = await fetch('/api/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (data.success) {
                showToast('Код отправлен на почту', 'success');
                closeForgotModal();
                openResetCodeModal();
                window.resetEmail = email;
            } else {
                showToast(data.error, 'error');
            }
        });

        document.getElementById('resetCodeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const code = document.getElementById('resetCode').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirm = document.getElementById('confirmNewPassword').value;
            if (newPassword !== confirm) { showToast('Пароли не совпадают', 'error'); return; }
            if (newPassword.length < 6) { showToast('Пароль минимум 6 символов', 'error'); return; }
            const res = await fetch('/api/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: window.resetEmail, code, new_password: newPassword })
            });
            const data = await res.json();
            if (data.success) {
                showToast('Пароль изменен! Войдите с новым паролем', 'success');
                closeResetCodeModal();
                openLoginModal();
            } else {
                showToast(data.error, 'error');
            }
        });
    </script>
</body>
</html>
'''

# ========== ЛИЧНЫЙ КАБИНЕТ ==========
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Личный кабинет - PriceMonitor</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f12; color: #e0e0e0; }
        .header { background: #0a0a0e; border-bottom: 1px solid #1e1e24; padding: 16px 0; position: sticky; top: 0; z-index: 100; }
        .container { max-width: 1400px; margin: 0 auto; padding: 0 24px; }
        .header-content { display: flex; justify-content: space-between; align-items: center; }
        .logo a { color: #fff; text-decoration: none; font-size: 20px; font-weight: 600; }
        .nav a { color: #a0a0b0; text-decoration: none; margin-left: 24px; cursor: pointer; }
        .nav a:hover { color: #fff; }
        .main { padding: 32px 0; }
        .card { background: #14141a; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #1e1e24; }
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #1e1e24; display: flex; justify-content: space-between; align-items: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
        .stat-card { background: linear-gradient(135deg, #1a1a24, #12121a); border: 1px solid #2a2a35; border-radius: 12px; padding: 20px; text-align: center; }
        .stat-value { font-size: 32px; font-weight: bold; margin: 8px 0; color: #fff; }
        .stat-label { font-size: 13px; color: #8a8a9a; text-transform: uppercase; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #a0a0b0; font-size: 13px; }
        .form-control { width: 100%; padding: 12px; background: #0f0f12; border: 1px solid #2a2a35; border-radius: 8px; color: #fff; font-size: 14px; }
        .form-control:focus { outline: none; border-color: #4a4a60; }
        .btn { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .btn-primary { background: #2a2a35; color: #fff; border: 1px solid #3a3a48; }
        .btn-primary:hover { background: #3a3a48; }
        .btn-success { background: #1a3a2a; color: #8cd4a0; border: 1px solid #2a4a3a; }
        .btn-danger { background: #3a1a1a; color: #f0a0a0; border: 1px solid #4a2a2a; }
        .result-box { background: #0f0f12; border-radius: 8px; padding: 20px; margin-top: 20px; display: none; border: 1px solid #2a2a35; text-align: center; }
        .price-big { font-size: 36px; font-weight: bold; color: #8cd4a0; margin: 10px 0; }
        .alert { padding: 12px; border-radius: 8px; margin-bottom: 16px; }
        .alert-success { background: #1a2a1a; color: #8cd4a0; border-left: 3px solid #8cd4a0; }
        .alert-error { background: #2a1a1a; color: #f0a0a0; border-left: 3px solid #f0a0a0; }
        .alert-warning { background: #2a2a1a; color: #e0d080; border-left: 3px solid #e0d080; }
        .tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid #1e1e24; }
        .tab { padding: 12px 24px; cursor: pointer; border: none; background: none; font-size: 14px; color: #8a8a9a; }
        .tab:hover { color: #fff; }
        .tab.active { color: #fff; border-bottom: 2px solid #fff; margin-bottom: -1px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .competitors-table { width: 100%; border-collapse: collapse; }
        .competitors-table th, .competitors-table td { padding: 12px; text-align: left; border-bottom: 1px solid #1e1e24; }
        .competitors-table th { color: #8a8a9a; font-weight: normal; font-size: 12px; }
        .api-key { background: #0f0f12; padding: 12px; border-radius: 8px; font-family: monospace; border: 1px solid #2a2a35; word-break: break-all; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }
        .modal-content { background: #14141a; margin: 80px auto; max-width: 500px; border-radius: 12px; padding: 28px; border: 1px solid #2a2a35; }
        #profileMenu { display: none; position: absolute; right: 24px; top: 70px; background: #14141a; border-radius: 8px; min-width: 180px; border: 1px solid #2a2a35; z-index: 1000; }
        #profileMenu a { display: block; padding: 12px 20px; color: #e0e0e0; text-decoration: none; border-bottom: 1px solid #1e1e24; }
        #profileMenu a:hover { background: #1a1a24; }
        #profileMenu a:last-child { border-bottom: none; color: #f0a0a0; }
        @media (max-width: 768px) { .stats-grid { grid-template-columns: 1fr; } .tabs { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo"><a href="/">PriceMonitor</a></div>
                <div class="nav">
                    <a onclick="showTab('dashboard')">Дашборд</a>
                    <a onclick="showTab('competitors')">Конкуренты</a>
                    <a onclick="showTab('history')">История</a>
                    <a id="profileBtn">Профиль</a>
                </div>
            </div>
        </div>
    </div>
    <div id="profileMenu">
        <a onclick="showTab('profile'); closeMenu()">Мой профиль</a>
        <a href="/logout">Выход</a>
    </div>

    <div class="main">
        <div class="container">
            <div id="alertContainer"></div>

            <div class="tabs">
                <button class="tab active" onclick="showTab('dashboard')">Дашборд</button>
                <button class="tab" onclick="showTab('competitors')">Конкуренты</button>
                <button class="tab" onclick="showTab('history')">История</button>
                <button class="tab" onclick="showTab('profile')">Профиль</button>
            </div>

            <div id="dashboardTab" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-value" id="totalCompetitors">0</div><div class="stat-label">Конкурентов</div></div>
                    <div class="stat-card"><div class="stat-value" id="totalParses">0</div><div class="stat-label">Проверок</div></div>
                    <div class="stat-card"><div class="stat-value" id="requestsLeft">1</div><div class="stat-label">Доступно запросов</div></div>
                </div>

                <div class="card">
                    <div class="card-title">Быстрая проверка конкурента</div>
                    <div class="form-group">
                        <label>Платформа</label>
                        <select id="platform" class="form-control">
                            <option value="avito">Avito</option>
                            <option value="ozon">Ozon</option>
                            <option value="wildberries">Wildberries</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Ссылка на товар</label>
                        <input type="text" id="url" class="form-control" placeholder="https://www.avito.ru/...">
                    </div>
                    <button class="btn btn-primary" onclick="checkPrice()">Проверить цену</button>
                    <div id="result" class="result-box"></div>
                </div>
            </div>

            <div id="competitorsTab" class="tab-content">
                <div class="card">
                    <div class="card-title">Список конкурентов <button class="btn btn-success" onclick="showAddModal()">+ Добавить</button></div>
                    <table class="competitors-table">
                        <thead><tr><th>Название</th><th>Платформа</th><th>Моя цена</th><th>Действия</th></tr></thead>
                        <tbody id="competitorsList"></tbody>
                    </table>
                </div>
            </div>

            <div id="historyTab" class="tab-content">
                <div class="card">
                    <div class="card-title">История проверок <button class="btn btn-primary" onclick="exportExcel()">Экспорт</button></div>
                    <table class="competitors-table">
                        <thead><tr><th>Дата</th><th>Конкурент</th><th>Платформа</th><th>Цена</th></tr></thead>
                        <tbody id="historyList"></tbody>
                    </table>
                </div>
            </div>

            <div id="profileTab" class="tab-content">
                <div class="card">
                    <div class="card-title">Личная информация</div>
                    <div class="form-group"><label>Email</label><input type="email" id="profileEmail" class="form-control" readonly></div>
                    <div class="form-group"><label>Полное имя</label><input type="text" id="profileName" class="form-control"></div>
                    <div class="form-group"><label>Телефон</label><input type="tel" id="profilePhone" class="form-control"></div>
                    <div class="form-group"><label>API ключ</label><div class="api-key" id="apiKey"></div></div>
                    <button class="btn btn-primary" onclick="saveProfile()">Сохранить</button>
                </div>
            </div>
        </div>
    </div>

    <div id="addModal" class="modal">
        <div class="modal-content">
            <h2>Добавить конкурента</h2>
            <div class="form-group"><label>Название</label><input type="text" id="compName" class="form-control"></div>
            <div class="form-group"><label>Платформа</label><select id="compPlatform" class="form-control"><option value="avito">Avito</option><option value="ozon">Ozon</option><option value="wildberries">Wildberries</option></select></div>
            <div class="form-group"><label>Ссылка</label><input type="text" id="compUrl" class="form-control"></div>
            <div class="form-group"><label>Моя цена</label><input type="number" id="compMyPrice" class="form-control"></div>
            <button class="btn btn-primary" onclick="addCompetitor()">Добавить</button>
            <button class="btn" onclick="closeModal()">Отмена</button>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
            event.target.classList.add('active');
            if (tabName === 'dashboard') { loadStats(); }
            if (tabName === 'competitors') { loadCompetitors(); }
            if (tabName === 'history') { loadHistory(); }
            if (tabName === 'profile') { loadProfile(); }
        }

        document.getElementById('profileBtn')?.addEventListener('click', function(e) {
            e.preventDefault();
            var menu = document.getElementById('profileMenu');
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        });

        function closeMenu() { document.getElementById('profileMenu').style.display = 'none'; }

        document.addEventListener('click', function(event) {
            var menu = document.getElementById('profileMenu');
            var btn = document.getElementById('profileBtn');
            if (menu && btn && !btn.contains(event.target) && !menu.contains(event.target)) {
                menu.style.display = 'none';
            }
        });

        async function loadStats() {
            const r = await fetch('/api/stats');
            const d = await r.json();
            document.getElementById('totalCompetitors').innerText = d.total_competitors || 0;
            document.getElementById('totalParses').innerText = d.total_parses || 0;
            document.getElementById('requestsLeft').innerText = d.requests_left === 'unlimited' ? '∞' : d.requests_left;
        }

        async function loadCompetitors() {
            const r = await fetch('/api/competitors');
            const list = await r.json();
            const tbody = document.getElementById('competitorsList');
            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">Нет добавленных конкурентов</td></tr>';
                return;
            }
            tbody.innerHTML = list.map(c => `
                <tr>
                    <td>${c.name}</td>
                    <td>${c.platform}</td>
                    <td>${c.my_price ? c.my_price + ' ₽' : '—'}</td>
                    <td><button class="btn btn-danger" onclick="deleteComp(${c.id})">Удалить</button></td>
                </tr>
            `).join('');
        }

        async function loadHistory() {
            const r = await fetch('/api/history');
            const list = await r.json();
            const tbody = document.getElementById('historyList');
            if (list.length === 0) {
                tbody.innerHTML = '<td><td colspan="4">Нет проверок</tr>';
                return;
            }
            tbody.innerHTML = list.map(h => `
                <tr>
                    <td>${new Date(h.date).toLocaleString()}</td>
                    <td>${h.name}</td>
                    <td>${h.platform}</td>
                    <td>${h.price} ₽</td>
                </tr>
            `).join('');
        }

        async function loadProfile() {
            const r = await fetch('/api/profile');
            const p = await r.json();
            document.getElementById('profileEmail').value = p.email;
            document.getElementById('profileName').value = p.full_name || '';
            document.getElementById('profilePhone').value = p.phone || '';
            document.getElementById('apiKey').innerText = p.api_key;
        }

        async function saveProfile() {
            const data = { full_name: document.getElementById('profileName').value, phone: document.getElementById('profilePhone').value };
            await fetch('/api/profile', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            showAlert('Профиль сохранён', 'success');
        }

        async function checkPrice() {
            const platform = document.getElementById('platform').value;
            const url = document.getElementById('url').value;
            const resultDiv = document.getElementById('result');
            if (!url) { showAlert('Введите ссылку', 'warning'); return; }
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = 'Загрузка...';
            try {
                const r = await fetch('/api/parse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ platform, url }) });
                const data = await r.json();
                if (r.ok && data.price) {
                    resultDiv.innerHTML = `<div class="price-big">${data.price.toLocaleString()} ₽</div><div>Цена успешно получена</div>`;
                    showAlert('Проверка выполнена', 'success');
                    loadStats(); loadHistory();
                } else if (r.status === 403) {
                    resultDiv.innerHTML = `<div style="color: #f0a0a0">${data.error}</div>`;
                    showAlert(data.error, 'warning');
                } else {
                    resultDiv.innerHTML = `<div style="color: #f0a0a0">${data.error || 'Не удалось найти цену'}</div>`;
                }
            } catch(e) { resultDiv.innerHTML = '<div style="color: #f0a0a0">Ошибка подключения</div>'; }
        }

        async function addCompetitor() {
            const data = { name: document.getElementById('compName').value, platform: document.getElementById('compPlatform').value, url: document.getElementById('compUrl').value, my_price: parseFloat(document.getElementById('compMyPrice').value) || 0 };
            if (!data.name || !data.url) { showAlert('Заполните поля', 'warning'); return; }
            const r = await fetch('/api/competitors', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if (r.ok) { showAlert('Конкурент добавлен', 'success'); closeModal(); loadCompetitors(); loadStats(); }
        }

        async function deleteComp(id) { if (!confirm('Удалить?')) return; await fetch(`/api/competitors/${id}`, { method: 'DELETE' }); loadCompetitors(); loadStats(); }

        async function exportExcel() { window.location.href = '/api/export/excel'; showAlert('Экспорт начат', 'success'); }

        function showAlert(msg, type) { const a = document.getElementById('alertContainer'); a.innerHTML = `<div class="alert alert-${type}">${msg}</div>`; setTimeout(() => a.innerHTML = '', 3000); }
        function showAddModal() { document.getElementById('addModal').style.display = 'block'; }
        function closeModal() { document.getElementById('addModal').style.display = 'none'; }

        loadStats(); loadCompetitors(); loadHistory();
    </script>
</body>
</html>
'''

# ========== СТРАНИЦЫ РЕГИСТРАЦИИ, ВХОДА, ПОДТВЕРЖДЕНИЯ ==========
VERIFY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Подтверждение email - PriceMonitor</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh}
    .card{background:#14141a;padding:40px;border-radius:16px;width:350px;border:1px solid #2a2a35;text-align:center}
    input{width:100%;padding:12px;margin:10px 0;background:#0f0f12;border:1px solid #2a2a35;border-radius:8px;color:#fff;text-align:center;font-size:20px;letter-spacing:5px}
    button{width:100%;padding:12px;background:#2a2a35;color:#fff;border:none;border-radius:8px;cursor:pointer}
    .error{color:#f0a0a0;margin-bottom:15px}
    a{color:#a0a0b0}
</style></head>
<body><div class="card"><h2>Подтверждение email</h2><p>Код отправлен на <strong>{{ email }}</strong></p>{% if error %}<div class="error">{{ error }}</div>{% endif %}<form method="post"><input type="text" name="code" placeholder="Код из письма" maxlength="6" autocomplete="off"><button type="submit">Подтвердить</button></form><a href="/resend-code">Отправить код повторно</a></div></body>
</html>
'''


LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Вход - PriceMonitor</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;position:relative}
    body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 20% 50%,rgba(30,30,60,0.4) 0%,transparent 60%),radial-gradient(circle at 80% 80%,rgba(60,40,80,0.3) 0%,transparent 60%);z-index:-1}
    .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:350px;border:1px solid rgba(42,42,53,0.5)}
    input{width:100%;padding:12px;margin:10px 0;background:rgba(15,15,18,0.8);border:1px solid #2a2a35;border-radius:8px;color:#fff}
    button{width:100%;padding:12px;background:#2a2a35;color:#fff;border:none;border-radius:8px;cursor:pointer}
    a{color:#a0a0b0;text-decoration:none}
    .header-buttons{display:flex;justify-content:space-between;margin-bottom:20px}
    .btn-small{padding:5px 12px;font-size:12px;background:#1a1a24;border:1px solid #2a2a35;border-radius:6px;color:#a0a0b0;text-decoration:none}
    .btn-small:hover{background:#2a2a35;color:#fff}
    .forgot{text-align:right;margin-top:5px;font-size:12px}
    .forgot a{color:#6a6a7a}
    .forgot a:hover{color:#a0a0b0}
</style></head>
<body>
<div class="card">
    <div class="header-buttons">
        <a href="/" class="btn-small">← Главная</a>
    </div>
    <h2 style="text-align:center;margin-bottom:30px">Вход</h2>
    <form method="post">
        <input type="email" name="email" placeholder="Email" required>
        <input type="password" name="password" placeholder="Пароль" required>
        <div class="forgot"><a href="/forgot-password">Забыли пароль?</a></div>
        <button type="submit">Войти</button>
    </form>
    <div style="text-align:center;margin-top:20px"><a href="/register">Нет аккаунта? Зарегистрироваться</a></div>
</div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Регистрация - PriceMonitor</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;position:relative}
    body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 20% 50%,rgba(30,30,60,0.4) 0%,transparent 60%),radial-gradient(circle at 80% 80%,rgba(60,40,80,0.3) 0%,transparent 60%);z-index:-1}
    .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:350px;border:1px solid rgba(42,42,53,0.5)}
    input{width:100%;padding:12px;margin:10px 0;background:rgba(15,15,18,0.8);border:1px solid #2a2a35;border-radius:8px;color:#fff}
    button{width:100%;padding:12px;background:#2a2a35;color:#fff;border:none;border-radius:8px;cursor:pointer}
    a{color:#a0a0b0;text-decoration:none}
    .header-buttons{display:flex;justify-content:space-between;margin-bottom:20px}
    .btn-small{padding:5px 12px;font-size:12px;background:#1a1a24;border:1px solid #2a2a35;border-radius:6px;color:#a0a0b0;text-decoration:none}
    .btn-small:hover{background:#2a2a35;color:#fff}
</style></head>
<body>
<div class="card">
    <div class="header-buttons">
        <a href="/" class="btn-small">← Главная</a>
    </div>
    <h2 style="text-align:center;margin-bottom:20px">Регистрация</h2>
    <form method="post">
        <input type="text" name="full_name" placeholder="Имя">
        <input type="email" name="email" placeholder="Email" required>
        <input type="tel" name="phone" placeholder="Телефон">
        <input type="password" name="password" placeholder="Пароль" required>
        <input type="password" name="confirm_password" placeholder="Подтвердите пароль" required>
        <button type="submit">Зарегистрироваться</button>
    </form>
    <div style="text-align:center;margin-top:20px"><a href="/login">Уже есть аккаунт? Войти</a></div>
</div>
</body>
</html>
'''


# ========== МАРШРУТЫ ==========
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')

        if password != confirm:
            return 'Пароли не совпадают'
        if len(password) < 6:
            return 'Пароль минимум 6 символов'

        user_id, code = db.register_user(email, password, full_name, phone)
        if user_id:
            send_verification_email(email, code)
            session['temp_email'] = email
            return redirect(url_for('verify_email'))
        return f'Ошибка: {code}'

    return render_template_string(REGISTER_TEMPLATE)


@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if 'temp_email' not in session:
        return redirect(url_for('register'))

    email = session['temp_email']

    if request.method == 'POST':
        code = request.form['code']

        if db.verify_email(email, code):
            session.pop('temp_email', None)
            conn = db.conn
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user_id = cursor.fetchone()[0]
            session['user_id'] = user_id
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(VERIFY_TEMPLATE, email=email, error="Неверный код")

    return render_template_string(VERIFY_TEMPLATE, email=email)


@app.route('/resend-code')
def resend_code():
    if 'temp_email' in session:
        email = session['temp_email']
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute('SELECT verification_code FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        if result and result[0]:
            send_verification_email(email, result[0])
    return redirect(url_for('verify_email'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user, error = db.verify_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))
        return f'Ошибка: {error}'

    return render_template_string(LOGIN_TEMPLATE)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE, email=session['email'])


@app.route('/api/parse', methods=['POST'])
@login_required
def api_parse():
    data = request.json
    platform = data.get('platform')
    url = data.get('url')

    if not url:
        return jsonify({'error': 'Введите ссылку'}), 400

    can_access, reason = db.can_make_request(session['user_id'])
    if not can_access:
        return jsonify({'error': reason}), 403

    result = parser.parse(platform, url)

    if result and result.get('price'):
        db.use_request(session['user_id'])
        return jsonify(result)

    return jsonify({'error': 'Не удалось найти цену'}), 404


@app.route('/api/competitors', methods=['GET'])
@login_required
def api_get_competitors():
    return jsonify(db.get_competitors(session['user_id']))


@app.route('/api/competitors', methods=['POST'])
@login_required
def api_add_competitor():
    data = request.json
    comp_id = db.add_competitor(session['user_id'], data['name'], data['platform'], data['url'],
                                data.get('my_price', 0))
    return jsonify({'id': comp_id})


@app.route('/api/competitors/<int:comp_id>', methods=['DELETE'])
@login_required
def api_delete_competitor(comp_id):
    db.delete_competitor(comp_id, session['user_id'])
    return jsonify({'status': 'ok'})


@app.route('/api/history')
@login_required
def api_history():
    return jsonify(db.get_history(session['user_id']))


@app.route('/api/stats')
@login_required
def api_stats():
    stats = db.get_stats(session['user_id'])
    can_access, reason = db.can_make_request(session['user_id'])
    if can_access and reason == 'active_subscription':
        stats['requests_left'] = 'unlimited'
    else:
        stats['requests_left'] = 1 - stats.get('free_used', 0)
        if stats['requests_left'] < 0:
            stats['requests_left'] = 0
    return jsonify(stats)


@app.route('/api/profile', methods=['GET'])
@login_required
def api_profile():
    return jsonify(db.get_user_profile(session['user_id']))


@app.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    data = request.json
    db.update_profile(session['user_id'], data.get('full_name'), data.get('phone'))
    return jsonify({'status': 'ok'})


@app.route('/api/export/excel')
@login_required
def export_excel():
    import io
    import csv

    history = db.get_history(session['user_id'])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Дата', 'Конкурент', 'Платформа', 'Цена'])
    for h in history:
        writer.writerow([h['date'], h['name'], h['platform'], h['price']])

    response = output.getvalue()
    return response, 200, {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename=price_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    }


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user, error = db.verify_user(email, password)
    if user:
        session['user_id'] = user['id']
        session['email'] = user['email']
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': error}), 401


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    phone = data.get('phone', '')

    user_id, code = db.register_user(email, password, name, phone)
    if user_id:
        send_verification_email(email, code)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': code}), 400


@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.json
    email = data.get('email')

    import random
    reset_code = ''.join(random.choices('0123456789', k=6))
    expires_at = datetime.now() + timedelta(minutes=15)

    conn = db.conn
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'error': 'Email не найден'}), 404

    cursor.execute('UPDATE users SET reset_code = ?, reset_code_expires = ? WHERE id = ?',
                   (reset_code, expires_at, user[0]))
    conn.commit()

    # Отправка письма
    subject = "Восстановление пароля - PriceMonitor"
    body = f"Ваш код: {reset_code}"
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Ошибка: {e}")

    return jsonify({'success': True})


@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')

    conn = db.conn
    cursor = conn.cursor()
    cursor.execute('SELECT id, reset_code, reset_code_expires FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404

    if user[1] != code:
        return jsonify({'success': False, 'error': 'Неверный код'}), 400

    if user[2]:
        try:
            expires = datetime.strptime(user[2], '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() > expires:
                return jsonify({'success': False, 'error': 'Код истёк'}), 400
        except:
            pass

    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000).hex()

    cursor.execute(
        'UPDATE users SET password_hash = ?, salt = ?, reset_code = NULL, reset_code_expires = NULL WHERE id = ?',
        (password_hash, salt, user[0]))
    conn.commit()

    return jsonify({'success': True})

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Проверяем, существует ли пользователь
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            # Генерируем код восстановления
            import random
            reset_code = ''.join(random.choices('0123456789', k=6))

            # Время истечения - через 15 минут
            expires_at = datetime.now() + timedelta(minutes=15)

            # Сохраняем код в базу (как текст, без форматирования)
            cursor.execute('UPDATE users SET reset_code = ?, reset_code_expires = ? WHERE id = ?',
                           (reset_code, expires_at.strftime('%Y-%m-%d %H:%M:%S'), user[0]))
            conn.commit()

            # Отправляем код на почту
            subject = "Восстановление пароля - PriceMonitor"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Восстановление пароля</h2>
                <p>Ваш код для сброса пароля: <strong style="font-size: 24px; color: #667eea;">{reset_code}</strong></p>
                <p>Введите этот код на странице восстановления пароля.</p>
                <p>Код действителен 15 минут.</p>
                <hr>
                <p>Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.</p>
                <p>С уважением,<br>Команда PriceMonitor</p>
            </body>
            </html>
            """

            try:
                msg = MIMEMultipart()
                msg['From'] = SMTP_USER
                msg['To'] = email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html', 'utf-8'))
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()

                # Сохраняем email в сессию для следующего шага
                session['reset_email'] = email

                return render_template_string(RESET_CODE_TEMPLATE, email=email)

            except Exception as e:
                print(f"Ошибка отправки: {e}")
                return 'Ошибка при отправке письма. Попробуйте позже.'
        else:
            return 'Пользователь с таким email не найден'

    return render_template_string(FORGOT_TEMPLATE)


# Шаблон для ввода кода
RESET_CODE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Введите код</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;position:relative}
    body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 20% 50%,rgba(30,30,60,0.4) 0%,transparent 60%),radial-gradient(circle at 80% 80%,rgba(60,40,80,0.3) 0%,transparent 60%);z-index:-1}
    .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:380px;border:1px solid rgba(42,42,53,0.5);text-align:center}
    input{width:100%;padding:12px;margin:10px 0;background:rgba(15,15,18,0.8);border:1px solid #2a2a35;border-radius:8px;color:#fff;text-align:center;font-size:20px;letter-spacing:5px}
    button{width:100%;padding:12px;background:#2a2a35;color:#fff;border:none;border-radius:8px;cursor:pointer;margin-top:10px}
    a{color:#a0a0b0;text-decoration:none}
    .header-buttons{text-align:left;margin-bottom:20px}
    .btn-small{padding:5px 12px;font-size:12px;background:#1a1a24;border:1px solid #2a2a35;border-radius:6px;color:#a0a0b0;text-decoration:none}
    .btn-small:hover{background:#2a2a35;color:#fff}
</style></head>
<body>
<div class="card">
    <div class="header-buttons"><a href="/login" class="btn-small">← Назад</a></div>
    <h2>Введите код</h2>
    <p>Код отправлен на <strong>{{ email }}</strong></p>
    <form method="post" action="/reset-password">
        <input type="text" name="code" placeholder="Код из письма" maxlength="6" autocomplete="off">
        <input type="password" name="new_password" placeholder="Новый пароль">
        <input type="password" name="confirm_password" placeholder="Подтвердите пароль">
        <button type="submit">Сбросить пароль</button>
    </form>
    <div style="margin-top:20px">
        <a href="/forgot-password">Отправить код повторно</a>
    </div>
</div>
</body>
</html>
'''

FORGOT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Восстановление пароля</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;position:relative}
    body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 20% 50%,rgba(30,30,60,0.4) 0%,transparent 60%),radial-gradient(circle at 80% 80%,rgba(60,40,80,0.3) 0%,transparent 60%);z-index:-1}
    .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:350px;border:1px solid rgba(42,42,53,0.5)}
    input{width:100%;padding:12px;margin:10px 0;background:rgba(15,15,18,0.8);border:1px solid #2a2a35;border-radius:8px;color:#fff}
    button{width:100%;padding:12px;background:#2a2a35;color:#fff;border:none;border-radius:8px;cursor:pointer}
    a{color:#a0a0b0;text-decoration:none}
    .header-buttons{margin-bottom:20px}
    .btn-small{padding:5px 12px;font-size:12px;background:#1a1a24;border:1px solid #2a2a35;border-radius:6px;color:#a0a0b0;text-decoration:none}
    .btn-small:hover{background:#2a2a35;color:#fff}
</style></head>
<body>
<div class="card">
    <div class="header-buttons"><a href="/login" class="btn-small">← Назад</a></div>
    <h2 style="text-align:center;margin-bottom:30px">Восстановление пароля</h2>
    <form method="post">
        <input type="email" name="email" placeholder="Email" required>
        <button type="submit">Отправить код</button>
    </form>
    <div style="text-align:center;margin-top:20px"><a href="/login">Вернуться ко входу</a></div>
</div>
</body>
</html>
'''


@app.route('/reset-password', methods=['POST'])
def reset_password():
    import hashlib  # <--- добавьте эту строку внутри функции

    code = request.form.get('code')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    email = session.get('reset_email')

    if not email:
        return redirect(url_for('forgot_password'))

    if new_password != confirm_password:
        return render_template_string(ERROR_TEMPLATE, error="Пароли не совпадают")

    if len(new_password) < 6:
        return render_template_string(ERROR_TEMPLATE, error="Пароль должен быть минимум 6 символов")

    # Проверяем код
    conn = db.conn
    cursor = conn.cursor()
    cursor.execute('SELECT id, reset_code, reset_code_expires FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        return render_template_string(ERROR_TEMPLATE, error="Пользователь не найден")

    if user[1] != code:
        return render_template_string(ERROR_TEMPLATE, error="Неверный код восстановления")

    # Проверяем, не истёк ли код
    if user[2]:
        try:
            expires = datetime.strptime(user[2], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expires:
                return render_template_string(ERROR_TEMPLATE, error="Код истёк. Запросите новый")
        except:
            pass

    # Обновляем пароль
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000).hex()

    cursor.execute(
        'UPDATE users SET password_hash = ?, salt = ?, reset_code = NULL, reset_code_expires = NULL WHERE id = ?',
        (password_hash, salt, user[0]))
    conn.commit()

    session.pop('reset_email', None)

    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Пароль изменен</title><meta charset="UTF-8"><style>
        body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh}
        .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:350px;text-align:center}
        .btn{display:inline-block;padding:12px 24px;background:#2a2a35;color:#fff;text-decoration:none;border-radius:8px;margin-top:20px}
        .btn:hover{background:#3a3a48}
    </style></head>
    <body>
    <div class="card">
        <h2>✅ Пароль успешно изменен!</h2>
        <p>Теперь вы можете войти с новым паролем.</p>
        <a href="/login" class="btn">Войти</a>
    </div>
    </body>
    </html>
    '''


ERROR_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Ошибка</title><meta charset="UTF-8"><style>
    body{background:#0a0a0e;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh}
    .card{background:rgba(20,20,26,0.8);backdrop-filter:blur(10px);padding:40px;border-radius:16px;width:350px;text-align:center}
    .error{color:#f0a0a0;margin-bottom:20px}
    .btn{display:inline-block;padding:12px 24px;background:#2a2a35;color:#fff;text-decoration:none;border-radius:8px;margin-top:20px}
</style></head>
<body>
<div class="card">
    <h2>❌ Ошибка</h2>
    <p class="error">{{ error }}</p>
    <a href="/forgot-password" class="btn">Попробовать снова</a>
</div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
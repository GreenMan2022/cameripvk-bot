# bot.py
import logging
from http import HTTPStatus
from urllib.parse import urlparse

# Веб-сервер
from aiohttp import web

# Бот
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"  # ← Замени!
GROUP_ID = -1003033000994  # ← Замени!
PORT = 10000  # Render использует PORT из env

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Встроенный HTML ===
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Камеры Первоуральска</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #000; color: white; height: 100vh; overflow: hidden; }
    #feed { height: 100vh; overflow-y: auto; scroll-snap-type: y mandatory; }
    .camera-item { height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; scroll-snap-align: center; }
    .video-container { width: 100%; height: 70vh; background: #000; position: relative; display: flex; align-items: center; justify-content: center; border-radius: 8px; }
    video { max-width: 100%; max-height: 100%; object-fit: contain; }
    .play-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; }
    .play-overlay.hidden { opacity: 0; pointer-events: none; }
    .play-btn { background: #3a86ff; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 8px; cursor: pointer; }
    .status { font-size: 14px; color: #ccc; margin-top: 8px; }
    .info h3 { margin: 0 0 5px 0; font-size: 18px; }
    .report-fab { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; background: #3a86ff; color: white; border: none; border-radius: 50%; font-size: 24px; cursor: pointer; z-index: 100; display: flex; align-items: center; justify-content: center; }
    .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; display: flex; align-items: flex-end; }
    .modal { width: 100%; background: white; border-radius: 16px 16px 0 0; padding: 20px; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); transform: translateY(100%); transition: transform 0.3s ease; }
    .modal.active { transform: translateY(0); }
    label, select { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
    select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
    .submit-btn { background: #3a86ff; color: white; border: none; padding: 14px; font-size: 16px; border-radius: 8px; width: 100%; margin-top: 10px; }
    .confirm-modal { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); z-index: 1002; text-align: center; width: 80%; max-width: 300px; }
    .confirm-buttons { display: flex; gap: 10px; justify-content: center; margin-top: 15px; }
    .btn-yes, .btn-no { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; }
    .btn-yes { background: #3a86ff; color: white; }
    .btn-no { background: #ccc; color: #333; }
  </style>
</head>
<body>
  <div id="feed"></div>
  <button class="report-fab" id="reportBtn">📝</button>

  <div class="modal-overlay" id="overlay">
    <div class="modal" id="reportModal">
      <h3>Сообщить о событии</h3>
      <div class="form-group">
        <label for="eventType">Тип события</label>
        <select id="eventType">
          <option value="dtp">ДТП</option>
          <option value="dps">ДПС</option>
          <option value="proish">Происшествие</option>
          <option value="inter">Интересное</option>
        </select>
      </div>
      <div class="form-group">
        <label>Камера</label>
        <select id="cameraSelect" disabled><option>Загрузка...</option></select>
      </div>
      <button class="submit-btn" id="submitBtn">Отправить</button>
    </div>
  </div>

  <div class="confirm-modal" id="confirmModal" style="display: none;">
    <p>Отправить сообщение?</p>
    <div class="confirm-buttons">
      <button class="btn-yes" id="confirmYes">Да</button>
      <button class="btn-no" id="confirmNo">Нет</button>
    </div>
  </div>

  <script>
    const CAMERAS = [
      { id: 1, name: "Перекрёсток Емлина-Ленина", url: "https://video.interra.ru/glaz.naroda.38-e60a533a34/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHz8AV5bAgwb_bq4Q9BexUA3ze2E" },
      { id: 2, name: "Перекрёсток Ленина-Космонавтов", url: "https://video.interra.ru/glaz.naroda.69-88107b23ac/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAABMSk4SEGVZtDQ81gwVqeUBRBIXE" },
      // ... остальные камеры
    ];

    const feed = document.getElementById('feed');
    const reportBtn = document.getElementById('reportBtn');
    const overlay = document.getElementById('overlay');
    const reportModal = document.getElementById('reportModal');
    const cameraSelect = document.getElementById('cameraSelect');
    const eventType = document.getElementById('eventType');
    const submitBtn = document.getElementById('submitBtn');
    const confirmModal = document.getElementById('confirmModal');
    const confirmYes = document.getElementById('confirmYes');
    const confirmNo = document.getElementById('confirmNo');
    const tg = Telegram.WebApp;
    tg.expand();

    let ACTIVE_INDEX = null;

    // === Создаём ленту ===
    CAMERAS.forEach((cam, index) => {
      const item = document.createElement('div');
      item.className = 'camera-item';
      item.dataset.index = index;

      const container = document.createElement('div');
      container.className = 'video-container';
      container.dataset.index = index;

      const video = document.createElement('video');
      video.id = `camera-${index}`;
      video.setAttribute('playsinline', '');
      video.muted = true;

      const overlayEl = document.createElement('div');
      overlayEl.className = 'play-overlay';
      overlayEl.id = `overlay-${index}`;
      overlayEl.innerHTML = `
        <button class="play-btn" data-index="${index}">▶️ Воспроизвести</button>
        <div class="status">Остановлено</div>
      `;

      container.appendChild(video);
      container.appendChild(overlayEl);
      item.appendChild(container);

      const info = document.createElement('div');
      info.className = 'info';
      info.innerHTML = `<h3>${cam.name}</h3>`;
      item.appendChild(info);

      feed.appendChild(item);
    });

    // === Кнопки воспроизведения ===
    document.querySelectorAll('.play-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const index = parseInt(this.dataset.index);
        const video = document.getElementById(`camera-${index}`);
        const overlayEl = document.getElementById(`overlay-${index}`);
        const statusEl = overlayEl.querySelector('.status');

        if (ACTIVE_INDEX === index) {
          stopCamera(index);
          ACTIVE_INDEX = null;
          this.innerHTML = '▶️ Воспроизвести';
          statusEl.textContent = 'Остановлено';
          overlayEl.classList.remove('hidden');
        } else {
          if (ACTIVE_INDEX !== null) stopCamera(ACTIVE_INDEX);
          startCamera(index, video, overlayEl);
          ACTIVE_INDEX = index;
          this.innerHTML = '⏸️ Пауза';
          statusEl.textContent = 'Трансляция';
          overlayEl.classList.add('hidden');
        }
      });
    });

    function startCamera(index, video, overlayEl) {
      if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(CAMERAS[index].url);
        hls.attachMedia(video);
      } else {
        video.src = CAMERAS[index].url;
      }
    }

    function stopCamera(index) {
      const video = document.getElementById(`camera-${index}`);
      if (video) {
        video.pause();
        video.src = '';
      }
    }

    // === Модальное окно ===
    reportBtn.addEventListener('click', () => {
      cameraSelect.innerHTML = '';
      if (ACTIVE_INDEX !== null) {
        const cam = CAMERAS[ACTIVE_INDEX];
        const opt = document.createElement('option');
        opt.value = cam.id;
        opt.textContent = cam.name;
        cameraSelect.appendChild(opt);
      } else {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Нет активной камеры';
        cameraSelect.appendChild(opt);
      }
      overlay.style.display = 'flex';
      setTimeout(() => reportModal.classList.add('active'), 10);
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        reportModal.classList.remove('active');
        setTimeout(() => overlay.style.display = 'none', 300);
      }
    });

    submitBtn.addEventListener('click', () => {
      const type = eventType.value;
      const cameraId = cameraSelect.value;
      if (!type || !cameraId) {
        alert('Выберите тип события и камеру');
        return;
      }
      confirmModal.style.display = 'block';
    });

    confirmYes.addEventListener('click', () => {
      const type = eventType.value;
      const cameraId = cameraSelect.value;
      const camera = CAMERAS.find(c => c.id == cameraId);

      tg.sendData(JSON.stringify({
        type: type,
        camera: camera ? camera.name : 'неизвестна',
        timestamp: new Date().toISOString()
      }));

      confirmModal.style.display = 'none';
      reportModal.classList.remove('active');
      setTimeout(() => overlay.style.display = 'none', 300);
    });

    confirmNo.addEventListener('click', () => {
      confirmModal.style.display = 'none';
    });
  </script>
</body>
</html>"""

# === Веб-сервер ===
async def handle_html(request):
    return web.Response(text=HTML_TEMPLATE, content_type="text/html")

# === Бот: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен /start от {user.full_name} (ID: {user.id})")

    # URL будет автоматически: https://ваш-проект.onrender.com
    keyboard = [[InlineKeyboardButton("🎥 Открыть камеры", web_app={"url": f"https://{request.host}"})]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Добро пожаловать в систему камер Первоуральска!\n\n"
        "Нажмите кнопку ниже, чтобы начать просмотр и отправку событий.",
        reply_markup=reply_markup
    )

# === Обработка web_app_data ===
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.effective_message.web_app_data.data
        logger.info(f"📩 Получены данные: {data}")
        import json
        data = json.loads(data)
        event_type = data.get("type", "неизвестно")
        camera = data.get("camera", "неизвестна")
        timestamp = data.get("timestamp", "неизвестно")
        user = update.effective_user

        text = (
            f"🚨 <b>Событие:</b> {event_type}\n"
            f"📹 <b>Камера:</b> {camera}\n"
            f"👤 <b>Пользователь:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> {user.id}\n"
            f"🕒 <b>Время:</b> {timestamp}"
        )

        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
        await update.message.reply_text("✅ Событие успешно отправлено в группу!")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

# === Запуск веб-сервера ===
async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_html)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")

# === Запуск бота ===
async def main():
    await run_web_server()

    application = Application.builder().token(API_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    logger.info("🚀 Бот запущен")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

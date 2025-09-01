# bot.py
import logging
from http import HTTPStatus
from urllib.parse import urlparse

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"  # ← Замени!
GROUP_ID = -1003033000994  # ← Замени!
PORT = int("10000")  # Render передаст PORT через env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Встроенный HTML (всё в одном файле) ===
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
      { id: 3, name: "Перекрёсток Ленина-Космонавтов", url: "https://video.interra.ru/glaz.naroda.7-719cef05e8/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAGSqutK7EdeiLrB7rOERcX3Wts-q" },
      { id: 4, name: "Проспект Космонавтов, д. 19", url: "https://video.interra.ru/glaz.naroda.27-f7e81f7bce/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAO8-2_rSX0V2qDVJqjDxFP68eVEC" },
      { id: 5, name: "Перекрёсток у ТЦ МАРС", url: "https://video.interra.ru/glaz.naroda.9-ec155e8f81/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAABayd-WjYHvATlrPCoSRCB9Qhp7t" },
      { id: 6, name: "Перекрёсток Ильича-Космонавтов", url: "https://video.interra.ru/glaz.naroda.14-e22ee71ce0/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAFIbXU9oIOtGLTqz6DiX5-QogJFE" },
      { id: 7, name: "Набережная пруда", url: "https://video.interra.ru/glaz.naroda.25-4cc98d0789/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHRsHgp_0qihUk_HBzu17ck8D_Mh" },
      { id: 8, name: "Перекрёсток Ватутина-Советская", url: "https://video.interra.ru/glaz.naroda.21-19bcd33f7f/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAACI80V-ezRrkIeJGCOuiLqMO3L1t" },
      { id: 9, name: "Перекрёсток Ватутина-Малышева", url: "https://video.interra.ru/glaz.naroda.29-1c63155041/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAAA7leZJfczXfTUxqdcWm1UMTIYE" },
      { id: 10, name: "Площадь Победы", url: "https://video.interra.ru/glaz.naroda.8-c53ad07719/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAMLD72VML0zTKX93CIDenlWj9dKt" },
      { id: 11, name: "Площадь Победы", url: "https://video.interra.ru/glaz.naroda.6-e95ca11965/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAERg-Eq8wmNvtnbw14DBkGUbvN4L" },
      { id: 12, name: "Вход в парк", url: "https://video.interra.ru/glaz.naroda.49-8793eb0dfd/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAGjW16v09aaEopwcTjZLvfXQJM6m" },
      { id: 13, name: "Перекрёсток Ватутина-Герцена", url: "https://video.interra.ru/glaz.naroda.46-b14600392b/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHpTPCtN6QpR7RIyY4vRpTA9_ny7" },
      { id: 14, name: "Перекрёсток Ватутина-Папанинцев", url: "https://video.interra.ru/glaz.naroda.47-f3ebf6b95c/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJwfkzSpW2cCjiundMLGdO1LI5XW" },
      { id: 15, name: "Перекрёсток Ватутина-Володарского", url: "https://video.interra.ru/glaz.naroda.48-96160aaa09/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJJQBHdEhiU9vJNpfTYkNKLzmstk" },
      { id: 16, name: "Перекрёсток Ватутина-Гагарина", url: "https://video.interra.ru/glaz.naroda.33-fad92591aa/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAIa8SSqK1QMAsi8pjhoKshKM6xE8" },
      { id: 17, name: "Перекрёсток Чкалова-Ильича", url: "https://video.interra.ru/glaz.naroda.3-50c57ffd3e/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAEzXxV8plI46SBNwkpSd2yhh2ukr" },
      { id: 18, name: "Перекрёсток Чкалова-Герцена", url: "https://video.interra.ru/glaz.naroda.45-b9b0186773/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAKOgh_KQet820Aojm4hVAre5zr_Y" },
      { id: 19, name: "Перекрёсток Чкалова-Папанинцев", url: "https://video.interra.ru/glaz.naroda.61-93ff24e89c/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAOIKxHk6pLXSg7uzNTYQiziq1vv0" },
      { id: 20, name: "Перекрёсток Ленина-Береговая", url: "https://video.interra.ru/glaz.naroda.45-b9b0186773/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAKOgh_KQet820Aojm4hVAre5zr_Y" },
      { id: 21, name: "Перекрёсток Ленина-Чекистов", url: "https://video.interra.ru/glaz.naroda.4-f9c1801660/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAC6_-QWK7Oa_TX1NSSJE_HeyndsS" },
      { id: 22, name: "Перекрёсток Ленина-Ильича", url: "https://video.interra.ru/glaz.naroda.65-9259fce158/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAD4jfac0sy8Ay91TN-JfzCG_2kIT" },
      { id: 23, name: "Перекрёсток Ленина-Ильича-Трубников", url: "https://video.interra.ru/glaz.naroda.37-7fdf4aae90/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAMtG4TISG-aM51pFWZXAzETyJjBk" },
      { id: 24, name: "Перекрёсток Трубников-Герцена", url: "https://video.interra.ru/glaz.naroda.28-375f2cc29e/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAIoZ6VpaxgZ4XY5ziRR2M3WlfZ8G" },
      { id: 25, name: "Перекрёсток Трубников-Папанинцев", url: "https://video.interra.ru/glaz.naroda.30-9c8902aa36/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJBCgbnYpxS3mek33e5gRgkpUovi" },
      { id: 26, name: "Перекрёсток Трубников-Школьная", url: "https://video.interra.ru/glaz.naroda.30-9c8902aa36/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJBCgbnYpxS3mek33e5gRgkpUovi" },
      { id: 27, name: "Перекрёсток Трубников-Гагарина", url: "https://video.interra.ru/glaz.naroda.30-9c8902aa36/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJBCgbnYpxS3mek33e5gRgkpUovi" },
      { id: 28, name: "П. Хромпик, круговой перекрёсток", url: "https://video.interra.ru/glaz.naroda.30-9c8902aa36/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJBCgbnYpxS3mek33e5gRgkpUovi" },
      { id: 29, name: "Городок на Береговой 20", url: "https://video.interra.ru/glaz.naroda.30-9c8902aa36/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAJBCgbnYpxS3mek33e5gRgkpUovi" },
      { id: 30, name: "Перекрёсток Данилова-Чекистов", url: "https://video.interra.ru/glaz.naroda.41-689af1f0f5/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAIk2Oi2v6utpI-VnnCkOoTecKOBo" },
      { id: 31, name: "Перекрёсток Данилова-Краснодонцев", url: "https://video.interra.ru/glaz.naroda.40-70e440be67/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHiw7qBs2t__8Eh8QuInL9_7TbC9" },
      { id: 32, name: "Перекрёсток Строителей-Громовой", url: "https://video.interra.ru/glaz.naroda.18-5d5aa2fe13/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAO_LrHz5W9KkkYQHjF2usKCNFkq2" },
      { id: 33, name: "Перекрёсток Строителей-Краснодонцев", url: "https://video.interra.ru/glaz.naroda.39-1360aa09c3/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAALTmT7aXbt8EQvVoTSh6S6o0Yq3h" },
      { id: 34, name: "Перекрёсток Вайнера-Береговая", url: "https://video.interra.ru/glaz.naroda.35-34558b3c59/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAITInK__BfhI-SNrKd4BoSBIdiy6" },
      { id: 35, name: "Перекрёсток Вайнера-Кольцевая", url: "https://video.interra.ru/glaz.naroda.13-8ca559e5bd/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHnTWKNTMOM5rCvtiNGNm0myL4_i" },
      { id: 36, name: "Перекрёсток Вайнера-Громовой", url: "https://video.interra.ru/glaz.naroda.31-eea5bf8987/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAHOknDMgtjdyik3MonZ0V0XHxttc" },
      { id: 37, name: "Перекрёсток Вайнера-Краснодонцев", url: "https://video.interra.ru/glaz.naroda.34-2e2f52f277/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAKoTLdlQ49cUdhpTIjMbEaD81ObK" },
      { id: 38, name: "Ул. Вайнера, выезд от магазина СОМ", url: "https://video.interra.ru/glaz.naroda.32-22975f2b2d/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAK1URRjrl3ZVkEB2-TSQx9RWcfJ4" },
      { id: 39, name: "Рынок", url: "https://video.interra.ru/glaz.naroda.15-f1aebe0b86/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAE6FGwzY-dN05B6KQEcPQwJRO-If" },
      { id: 40, name: "Перекрёсток Вайнера-Ильича", url: "https://video.interra.ru/glaz.naroda.36-f4d80dd3cf/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAADTcF098EjzS7rQiDF-YOCAglQAS" },
      { id: 41, name: "Перекрёсток на улице Сантехизделий вблизи дома №28", url: "https://video.interra.ru/glaz.naroda.68-470580056f/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAAIZMKpITECzm_bsql7jK8SaZjKw" },
      { id: 42, name: "П. Динас, круговой перекрёсток", url: "https://video.interra.ru/glaz.naroda.11-067f37bc81/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAPHda2mNPXsjZy7VEGak5e4sOBnT" },
      { id: 43, name: "Перекрёсток Ильича - 50 лет СССР", url: "https://video.interra.ru/glaz.naroda.62-60daf9cda0/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAACVZ-BLGA3sQS9m7AZXB5Nqz6BUm" },
      { id: 44, name: "П. Динас, площадь", url: "https://video.interra.ru/glaz.naroda.62-60daf9cda0/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAACVZ-BLGA3sQS9m7AZXB5Nqz6BUm" },
      { id: 45, name: "Перекрёсток Талица - Сакко и Ванцетти", url: "https://video.interra.ru/glaz.naroda.17-49dca37237/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAH29iQD9IXRCc-cgdRIXudyocrpu" },
      { id: 46, name: "Перекрёсток Энгельса-Фурманова-Бурильщиков", url: "https://video.interra.ru/glaz.naroda.42-097dc52569/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAA_mpHJ8uHP2H9Q1Zbhd5732id8N" },
      { id: 47, name: "Перекрёсток Коммунистическая-Ленина", url: "https://video2.interra.ru/glaz.naroda.504-d8b2dcde14/tracks-v1/mono.m3u8?token=3.9CzUU5u-AAAAAAAAAEsAAAAAAAAAAOnSd-VAJBBftYpJxGc2KU8-Mcx2" }
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

# === Веб-сервер: раздаёт HTML ===
async def handle_html(request):
    return web.Response(text=HTML_TEMPLATE, content_type="text/html")

# === Бот: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен /start от {user.full_name} (ID: {user.id})")

    # Авто-определение HTTPS-ссылки
    host = request.host
    web_app_url = f"https://{host}"
    keyboard = [[InlineKeyboardButton("🎥 Открыть камеры", web_app={"url": web_app_url})]]
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
    loop = asyncio.get_event_loop()
    loop.create_task(main())

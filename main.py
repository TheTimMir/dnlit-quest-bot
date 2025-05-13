import json
import logging
import asyncio
from collections import defaultdict
from typing import Dict, List

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# ------------------- Логирование -------------------
file_handler = logging.FileHandler("bot.log", mode='a', encoding="utf-8")
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger()

# ------------------- Константы -------------------
TOKEN = "YOUR-TOKEN-HERE"
DATA_FILE = "data.json"
ADMIN_ID = -1 #YOUR-ADMIN-ID-HERE

reply_after_photo = (
    "🧭 Ваш наступний пункт — <b><i>найдавніший університет нашого міста</i></b>. "
    "Там ви маєте знайти людину, <b>яка своїм ремеслом дала поштовх до появи перших поселень на території міста Дніпро.</b>"
)

reply_after_institute = (
    "📚 Наступний крок — рушайте до вашої теперішньої <b>Alma Mater</b>. "
)

reply_after_mist = (
    "🖼️ Уважно вивчіть це зображення. Тут сховані фрагменти з творів, що не терплять спотворення. "
    "Знайдіть справжнє серед підробок."
)

reply_after_kazka = (
    "📖 Наступна зупинка — місце, де казки не просто живуть, а зберігаються на сторінках. "
    "Вирушайте туди, де оживає дитяча уява."
)

reply_after_code = (
    "📍 На карті вказано точку. Знайдіть місце, де зустрічаються дитячі спогади та рух. "
    "Воно зовсім поряд з тим, звідки все починалося..."
)

reply_after_crossroad = (
    "🛤️ Два шляхи перетинаються, як вірші на зображенні. "
    "Знайдіть місце, де ці шляхи ведуть до нових відкриттів."
)

valid_teams = {"9A", "9B", "10A", "10B", "10G"}
team_members = {}  # Загрузится через create_storage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# ------------------- Хранилище -------------------
def create_storage() -> Dict[str, List[int]]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return defaultdict(list, {k: list(set(v)) for k, v in raw.items()})
    except FileNotFoundError:
        return {
            "9A": [],
            "9B": [],
            "10A": [],
            "10B": [],
            "10G": [],
            "other": [],
            "admin": [admin_id],
        }


def save_storage(data: Dict[str, List[int]]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------- Хелпери -------------------
def add_user_to_team(team_code: str, user_id: int):
    if user_id not in team_members[team_code]:
        team_members[team_code].append(user_id)
        save_storage(team_members)
        logger.info("✅ Зарегистрирован пользователь %s в команду %s", user_id, team_code)


def get_user_team(user_id: int):
    for code, members in team_members.items():
        if user_id in members:
            return code
    return None


async def notify_team(team_code: str, text: str):
    for user_id in team_members.get(team_code, []):
        try:
            await bot.send_message(user_id, text, disable_web_page_preview=True)
        except Exception as e:
            logger.warning("⚠️ Не удалось отправить сообщение %s: %s", user_id, e)


def start_message(team_code: str) -> str:
    return (
        f"👋 Вітаємо у захопливому квесті <b>Освітній детектив ДНЛІТ: Таємниці Дніпра</b>! \n"
        f"Ваша команда: <b>{team_code}</b>\n\n"
        "📌 <b>Як працює бот?</b>\n"
        "Протягом квесту ви отримуватимете слова, коди чи комбінації. Надсилайте їх боту — "
        "у разі правильного введення ви отримаєте наступну підказку. Якщо код некоректний — бот повідомить про це.\n\n"
        "⚠️ <b>УВАГА: Під час повітряної тривоги квест зупиняється!</b> \n"
        "Команда повинна негайно пройти до найближчого укриття та чекати на відбій тривоги.\n\n"
        "🛡 <b>Місця укриттів:</b>\n"
        "• <b>Школа №67</b> - пров. Євгена Коновальця, 6 \n"
        "• <b>Нац. університет</b> - просп. Дмитра Яворницького, 19\n"
        "• <b>Дніпровський художній музей</b> - вул. Шевченка, 21\n"
        "• <b>ВолейКамп</b> - вул. Володимира Вернадського, 6\n"
        "‼️ У випадку, якщо щось не працює або виникла помилка — звертайтесь до координатора: @TheTimMir"
    )


# ------------------- Хендлери -------------------
router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def admin_approve(query: CallbackQuery):
    team_code = query.data.split("_")[1]
    await notify_team(team_code, reply_after_photo)
    await query.message.edit_caption("✅ Фото одобрено. Переходьте до наступного кроку.")


@router.callback_query(F.data.startswith("reject_"))
async def admin_reject(query: CallbackQuery):
    team_code = query.data.split("_")[1]
    await notify_team(team_code, "❌ Ваше фото відхилено. Спробуйте ще раз.")
    await query.message.edit_caption("❌ Фото відхилено.")


@router.message(F.text.casefold() == "інститут")
async def handle_institute_word(message: Message):
    logger.info("🏛️ Слово 'інститут' от %s", message.from_user.id)
    team_code = get_user_team(message.from_user.id)
    if not team_code:
        await message.answer("🚫 Ваша команда не зареєстрована.")
        return
    await notify_team(team_code, reply_after_institute)


@router.message(F.text.casefold() == "міст")
async def handle_mist(message: Message):
    team_code = get_user_team(message.from_user.id)
    logger.info("🖼️ Слово 'міст' от %s в команді %s", message.from_user.id, team_code)
    photo = FSInputFile("media/mist.jpg")
    await message.reply_photo(photo, caption=reply_after_crossroad)

@router.message(F.text.casefold() == "казка")
async def handle_kazka(message: Message):
    team_code = get_user_team(message.from_user.id)
    logger.info("📚 Слово 'казка' от %s в команді %s", message.from_user.id, team_code)
    if not team_code:
        await message.answer("🚫 Ваша команда не зареєстрована.")
        return
    await notify_team(team_code, reply_after_kazka)


@router.message(F.text.casefold().replace(" ", "").replace("\n", "") == "1е2г3д4б5а6в")
@router.message(F.text.casefold().replace(" ", "").replace("\n", "") == "егдбав")
async def handle_code(message: Message):
    team_code = get_user_team(message.from_user.id)
    logger.info("📦 Введено комбінацію от %s в команді %s", message.from_user.id, team_code)
    if not team_code:
        await message.answer("🚫 Ваша команда не зареєстрована.")
        return
    await notify_team(team_code, reply_after_code)
    latitude, longitude = 48.460187, 35.062562
    for user_id in team_members.get(team_code, []):
        try:
            await bot.send_location(user_id, latitude, longitude)
            logger.info("📍 Локация отправлена пользователю %s в команді %s", user_id, team_code)
        except Exception as e:
            logger.warning("⚠️ Не удалось отправить локацию %s в команді %s: %s", user_id, team_code, e)


@router.message(F.text.startswith("/start"))
async def handle_start(message: Message):
    parts = message.text.split()
    team_code = parts[1] if len(parts) > 1 else None
    user_id = message.from_user.id

    if not team_code or team_code not in valid_teams:
        if user_id not in team_members["other"]:
            team_members["other"].append(user_id)
            save_storage(team_members)
            logger.warning("❓ Пользователь %s попал в группу 'other'", user_id)
        await message.answer("⚠️ Ваша команда не розпізнана. Будь ласка, перескануйте QR-код вашої команди.")
        return

    add_user_to_team(team_code, user_id)
    logger.info("👋 Пользователь %s добавлен в команду %s", user_id, team_code)
    await message.answer(start_message(team_code))


@router.message(F.text.startswith("/bc"))
async def handle_admin_broadcast(message: Message):
    if message.from_user.id not in [admin_id]:
        await message.answer("❌ У вас немає прав для виконання цієї команди.")
        return
    text = message.text[len("/bc "):].strip()
    if not text:
        await message.answer("⚠️ Будь ласка, надайте текст повідомлення.")
        return
    coordinator_message = f"📢 Повідомлення від координатора: {text}"
    for team, members in team_members.items():
        for user_id in members:
            try:
                await bot.send_message(user_id, coordinator_message, disable_web_page_preview=True)
                logger.info("📢 Повідомлення надіслано користувачу %s в команді %s", user_id, team)
            except Exception as e:
                logger.warning("⚠️ Не вдалося надіслати повідомлення %s в команді %s: %s", user_id, team, e)
    await message.answer("✅ Повідомлення надіслано всім користувачам.")


@router.message(F.text.startswith("/msg"))
async def handle_team_notify(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Будь ласка, надайте код команди та текст повідомлення.")
        return
    team_code, text = parts[1], parts[2]
    if team_code not in valid_teams:
        await message.answer("❌ Невідомий код команди.")
        return
    coordinator_message = f"📢 Повідомлення від координатора: {text}"
    await notify_team(team_code, coordinator_message)
    logger.info("📢 Повідомлення надіслано команді %s", team_code)
    await message.answer(f"✅ Повідомлення надіслано команді {team_code}.")


@router.message(F.text.startswith("/list"))
async def handle_list_users(message: Message):
    if message.from_user.id not in [admin_id]:
        await message.answer("❌ У вас немає прав для виконання цієї команди.")
        return
    response = "📋 <b>Список зареєстрованих користувачів:</b>\n"
    for team, members in team_members.items():
        response += f"\n<b>Команда {team} ({len(members)}):</b>\n"
        if members:
            for user_id in members:
                try:
                    user = await bot.get_chat(user_id)
                    response += f"- {user.first_name} {user.last_name or ''} ({user_id})\n"
                    logger.info("👤 Користувач %s в команді %s: %s %s", user_id, team, user.first_name, user.last_name or '')
                except Exception as e:
                    logger.warning("⚠️ Не вдалося отримати дані користувача %s в команді %s: %s", user_id, team, e)
                    response += f"- {user_id} (невідомий користувач)\n"
        else:
            response += "Немає зареєстрованих користувачів."
        response += "\n"
    await message.answer(response, parse_mode=ParseMode.HTML)


@router.message(F.text.startswith("/rem"))
async def handle_remove_user(message: Message):
    if message.from_user.id not in [admin_id]:
        await message.answer("❌ У вас немає прав для виконання цієї команди.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Будь ласка, надайте ID користувача для переміщення.")
        return
    user_id = int(parts[1])
    moved = False
    for team, members in team_members.items():
        if user_id in members:
            members.remove(user_id)
            moved = True
            logger.info("👤 Користувач %s переміщений з команди %s до групи 'other'", user_id, team)
    if moved:
        team_members["other"].append(user_id)
        save_storage(team_members)
        await message.answer(f"✅ Користувач {user_id} переміщений до групи 'other'.")
    else:
        await message.answer("⚠️ Користувача не знайдено в жодній команді.")


@router.message(F.text.startswith("/add"))
async def handle_add_user(message: Message):
    if message.from_user.id not in [admin_id]:
        await message.answer("❌ У вас немає прав для виконання цієї команди.")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Будь ласка, надайте ID користувача та код команди.")
        return
    user_id, team_code = int(parts[1]), parts[2]
    if team_code not in valid_teams:
        await message.answer("❌ Невідомий код команди.")
        return
    if user_id not in team_members[team_code]:
        team_members[team_code].append(user_id)
        save_storage(team_members)
        await bot.send_message(user_id, f"✅ Ви додані до команди {team_code}.")
        # Notify admin about the new addition
        try:
            user = await bot.get_chat(user_id)
            admin_message = f"👤 {user.first_name} {user.last_name or ''} ({user_id}) доданий до команди {team_code}."
            await bot.send_message(admin_id, admin_message)
            logger.info("👤 Користувач %s доданий до команди %s: %s %s", user_id, team_code, user.first_name, user.last_name or '')
        except Exception as e:
            logger.warning("⚠️ Не вдалося отримати дані користувача %s в команді %s: %s", user_id, team_code, e)
        await message.answer(f"✅ Користувач {user_id} доданий до команди {team_code}.")
    else:
        await message.answer(f"⚠️ Користувач {user_id} вже є в команді {team_code}.")


@router.message(F.photo)
async def handle_admin_image(message: Message):
    team_code = get_user_team(message.from_user.id)
    if message.from_user.id != admin_id:
        logger.info("📸 Фото от %s в команді %s", message.from_user.id, team_code)
        if not team_code:
            await message.answer("🚫 Ваша команда не зареєстрована.")
            return
        await message.answer("⏳ Ваше фото на перевірці. Будь ласка, зачекайте.")
        approve_button = InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{team_code}")
        reject_button = InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{team_code}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[approve_button, reject_button]])
        await bot.send_photo(admin_id, message.photo[-1].file_id, caption=f"Фото от команды {team_code}. Одобрить?", reply_markup=keyboard)
        return
    
    team_code = message.caption.strip()
    
    for user_id in team_members.get(team_code, []):
        try:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=f"😉 Спробуйте розгадати цей ребус, що є правильним кодом.")
        except Exception as e:
            logger.warning("⚠️ Не удалось отправить фото %s: %s", user_id, e)
    
    await message.answer(f"✅ Фото надіслано команді {team_code}.")


@router.message(F.text)
async def fallback_handler(message: Message):
    team_code = get_user_team(message.from_user.id)
    logger.info("⚠️ Невідоме повідомлення від %s в команді %s: %s", message.from_user.id, team_code, message.text)
    await message.answer("⚠️ Щось не те. Можливо, ви ввели неправильний код або повідомлення.")


# ------------------- Main -------------------
async def main():
    global team_members
    logger.info("Main starting!")
    team_members = create_storage()

    for special in ("admin", "other"):
        if special not in team_members:
            team_members[special] = []

    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

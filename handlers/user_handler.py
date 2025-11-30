from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from translations import translations_messages as tm
from translations import translations_buttons as tb
import keyboards as kbs
import aiohttp, os, aiofiles, logging, re
from datetime import datetime
from db import User

class UserStates(StatesGroup):
    AWAITING_FILE_UPLOAD = State()
    AWAITING_TOKEN_INPUT = State()

router = Router()

async def check_token(user_token: str):
    async with aiohttp.ClientSession() as session:
        URL = "https://cloud.onlysq.ru/api/files"
        async with session.get(URL, cookies={"user_token": user_token}) as response:
            jsn = await response.json()
            return jsn.ok

async def upload_file(file_path: str, user_token: str):
    URL = "https://cloud.onlysq.ru/upload"
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field(
                'file',
                f,
                filename=os.path.basename(file_path),
                content_type='application/octet-stream'
            )
            async with session.post(URL, data=data, cookies={"user_token": user_token}) as response:
                logging.info(f"Upload response status: {response.status}; Json: {await response.text()}")
                if response.status == 200:
                    return await response.json()
                else:
                    return None
async def get_info_file(file_id: str, user_token: str):
    URL = f"https://cloud.onlysq.ru/api/files"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, cookies={"user_token": user_token}) as response:
            if response.status == 200:
                files = await response.json()
                for file in files:
                    if file['id'] == file_id:
                        return file
                return None
            else:
                return None

async def get_token_info(user_token: str):
    URL = "https://cloud.onlysq.ru/files"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, cookies={"user_token": user_token}) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

@router.message(Command("help"))
async def send_help(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()
    await message.edit_text(tm["help_message"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))

# region upload
@router.callback_query(F.data == "upload")
async def callback_upload(callback_query, state: FSMContext):
    language = callback_query.from_user.language_code

    user = await User.get(telegram_id=callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    
    await callback_query.message.edit_text(tm["upload_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_FILE_UPLOAD)
    await callback_query.answer()

@router.message(Command("upload"))
async def prompt_upload(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()

    if await User.filter(telegram_id=message.from_user.id).exists() is None:
        await User.create(telegram_id=message.from_user.id, created_at=datetime.utcnow(), user_token=None)
    
    user = await User.get(telegram_id=message.from_user.id)
    
    if user.user_token is None:
        await message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    
    await message.edit_text(tm["upload_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_FILE_UPLOAD)

# region my files
@router.callback_query(F.data == "myfiles")
async def callback_myfiles(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    await callback_query.message.edit_text(tm["geting_files"].get(language, "en"))
    user = await User.filter(telegram_id=callback_query.from_user.id).get()
    if user.user_token is None:
        await callback_query.message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    URL = "https://cloud.onlysq.ru/api/files"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, cookies={"user_token": user.user_token}) as response:
            if response.status == 200:
                files = await response.json()
                if not files:
                    await callback_query.message.edit_text(tm["no_files"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
                    return
                markup = kbs.get_files_keyboard(files, language)
                await callback_query.message.edit_text(tm["files"].get(language, "en"), reply_markup=markup)
            else:
                await callback_query.message.edit_text(tm["file_list_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await callback_query.answer()

@router.message(Command("myfiles"))
async def list_user_files(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()
    user = await User.filter(telegram_id=message.from_user.id).get()
    if user.user_token is None:
        await message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    URL = "https://cloud.onlysq.ru/api/files"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, cookies={"user_token": user.user_token}) as response:
            if response.status == 200:
                files = await response.json()
                if not files:
                    await message.edit_text(tm["no_files"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
                    return
                markup = kbs.get_files_keyboard(files, language)
                await message.edit_text(tm["files"][language].get(language, "en"), reply_markup=markup)
            else:
                await message.edit_text(tm["file_list_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))

# region menu
@router.callback_query(F.data == "menu")
async def callback_menu(callback_query: CallbackQuery, state: FSMContext):
    language = callback_query.from_user.language_code
    markup = kbs.get_welcome_keyboard(language)
    await callback_query.message.edit_text(tm["start_message"].get(language, "en"), reply_markup=markup)
    await callback_query.answer()
    await state.clear()

# region settings
@router.callback_query(F.data == "settings")
async def callback_settings(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    markup = kbs.get_settings_keyboard(language)
    user = await User.get(telegram_id=callback_query.from_user.id)
    user_token = user.user_token if user.user_token else "Not set"
    await callback_query.message.edit_text(tm["settings_message"].get(language, "en").format(user_token) , reply_markup=markup)
    await callback_query.answer()

# region set token
@router.callback_query(F.data == "settoken")
async def callback_settoken(callback_query: CallbackQuery, state: FSMContext):
    language = callback_query.from_user.language_code
    await state.clear()
    await callback_query.message.edit_text(tm["set_token_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_TOKEN_INPUT)
    await callback_query.answer()

@router.message(Command("settoken"))
async def set_user_token(message: Message):
    language = message.from_user.language_code
    try:
        token = message.text.split(" ")[1]
    except IndexError:
        await message.edit_text("Please provide a token. Usage: /settoken YOUR_TOKEN", reply_markup=kbs.get_menu_keyboard(language))
        return
    if not await check_token(token):
        await message.edit_text(tm["invalid_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    if await User.filter(telegram_id=message.from_user.id).exists() is None:
        await User.create(telegram_id=message.from_user.id, created_at=datetime.utcnow(), user_token=token)
    else:
        user = await User.get(telegram_id=message.from_user.id)
        user.user_token = token
        await user.save()
    
    await message.edit_text(tm["token_set_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))

# region awaiting file upload
@router.message(UserStates.AWAITING_FILE_UPLOAD)
async def handle_file_upload(message, state: FSMContext, bot: Bot):
    language = message.from_user.language_code
    if type(message) == CallbackQuery:
        message = message.message
    
    user = await User.filter(telegram_id=message.from_user.id).get()
    file_path = None
    
    try:
        os.makedirs("downloads", exist_ok=True)
        # Handle document
        if message.document:
            file_id = message.document.file_id
            file = await bot.get_file(file_id)
            if message.document.file_size > 2 * 1024 * 1024 * 1024:
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file_path = f"downloads/{message.document.file_name}"
            await bot.download_file(file.file_path, destination=file_path)
        
        # Handle photo
        elif message.photo:
            file_id = message.photo[-1].file_id
            file = await bot.get_file(file_id)
            if message.photo[-1].file_size > 2 * 1024 * 1024 * 1024:
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file_path = f"downloads/photo_{message.from_user.id}.jpg"
            await bot.download_file(file.file_path, destination=file_path)
        
        # Handle video
        elif message.video:
            file_id = message.video.file_id
            file = await bot.get_file(file_id)
            if message.video.file_size > 2 * 1024 * 1024 * 1024:
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file_path = f"downloads/video_{message.from_user.id}.mp4"
            await bot.download_file(file.file_path, destination=file_path)
        
        # Handle audio
        elif message.audio:
            file_id = message.audio.file_id
            file = await bot.get_file(file_id)
            if message.audio.file_size > 2 * 1024 * 1024 * 1024:
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file_path = f"downloads/audio_{message.from_user.id}.mp3"
            await bot.download_file(file.file_path, destination=file_path)
        
        # Handle text
        elif message.text:
            file_path = f"downloads/text_{message.from_user.id}.txt"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(message.text)
        
        else:
            await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
            await state.clear()
            return
        
        # Upload file to server
        response = await upload_file(file_path, user.user_token)
        if response and response.get("ok"):
            download_link = response.get("url", "N/A")
            _id = response.get("url").split("/")[-1]
            logging.info(f"File uploaded for user {message.from_user.id}: {response}")
            await message.answer(tm["upload_success"].get(language, "en").format(_id, download_link), reply_markup=kbs.get_menu_keyboard(language))
        else:
            await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        
        # Clean up
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    
    except Exception as e:
        logging.error(f"Upload error for user {message.from_user.id}: {e}")
        await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    
    await state.clear()

# region awaiting token input
@router.message(UserStates.AWAITING_TOKEN_INPUT)
async def handle_token_input(message: Message, state: FSMContext):
    language = message.from_user.language_code
    token = message.text.strip()
    if not await check_token(token):
        await message.answer(tm["invalid_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    if await User.filter(telegram_id=message.from_user.id).exists() is None:
        await User.create(telegram_id=message.from_user.id, created_at=datetime.utcnow(), user_token=token)
    else:
        user = await User.get(telegram_id=message.from_user.id)
        user.user_token = token
        await user.save()
    
    await message.answer(tm["token_set_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.clear()

# region file
@router.callback_query(F.data.startswith("file_"))
async def callback_file_details(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_id = callback_query.data.split("_")[1]
    download_link = f"https://cloud.onlysq.ru/file/{file_id}"
    file_info = await get_info_file(file_id, (await User.get(telegram_id=callback_query.from_user.id)).user_token)
    await callback_query.message.edit_text(
        tm["file_details"].get(language, "en").format(file_info['name'], file_info['views'], file_info['unique'], download_link),
        reply_markup=kbs.get_file_action_keyboard(file_id, language)
    )

@router.callback_query(F.data.startswith("download_"))
async def callback_file_download(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_id = callback_query.data.split("_")[1]
    download_link = f"https://cloud.onlysq.ru/file/{file_id}"
    file_info = await get_info_file(file_id, (await User.get(telegram_id=callback_query.from_user.id)).user_token)

    async with aiohttp.ClientSession() as session:
        async with session.get(download_link) as response:
            response.raise_for_status()
            content_disposition = response.headers.get('Content-Disposition')

            os.makedirs("downloads", exist_ok=True)
            destination_path = os.path.join("downloads", file_info['name'])

            try:
                async with aiofiles.open(destination_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                async with aiofiles.open(destination_path, 'rb') as file:
                    file_content = await file.read()
                file_content = BufferedInputFile(file_content, filename=file_info['name'])
                await callback_query.message.answer_document(document=file_content, filename=file_info['name'])
                os.remove(destination_path)
            except IOError as e:
                logging.error(f"Failed to write file {file_info['name']}: {e}")
                await callback_query.message.answer(tm["file_download_failure"].get(language, "en"))
    await callback_query.answer()

@router.callback_query(F.data.startswith("delete_"))
async def callback_file_delete(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_id = callback_query.data.split("_")[1]
    URL = f"https://cloud.onlysq.ru/file/{file_id}"
    user = await User.get(telegram_id=callback_query.from_user.id)
    file_info = await get_info_file(file_id, user.user_token)
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": file_info['owner_key']
        }
        async with session.delete(URL, headers=headers) as response:
            resp_json = await response.json()
            logging.info(f"Delete file response for user {callback_query.from_user.id}: {resp_json}")
            if resp_json.get("ok"):
                await callback_query.message.edit_text(tm["file_delete_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
            else:
                await callback_query.message.edit_text(tm["file_delete_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await callback_query.answer()

@router.callback_query(F.data == "generate_token")
async def callback_gentoken(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    user = await User.get(telegram_id=callback_query.from_user.id)
    async with aiohttp.ClientSession() as session:
        URL = "https://cloud.onlysq.ru/"
        async with session.get(URL) as response:
            if response.status == 200:
                cookies = response.cookies
                user_token = cookies.get("user_token").value
                user.user_token = user_token
                await user.save()
                await callback_query.message.edit_text(tm["token_generated_success"].get(language, "en").format(user_token), reply_markup=kbs.get_menu_keyboard(language))
            else:
                await callback_query.message.edit_text(tm["file_delete_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await callback_query.answer()
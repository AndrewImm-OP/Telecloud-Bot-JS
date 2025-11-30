from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from translations import translations_buttons as tb

def get_welcome_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["upload_button"][language], callback_data="upload"),
            InlineKeyboardButton(text=tb["my_files_button"][language], callback_data="myfiles")
        ],
        [
            InlineKeyboardButton(text=tb["settings_button"][language], callback_data="settings")
        ]
    ])
    return keyboard

def get_files_keyboard(files, language: str = "en") -> InlineKeyboardMarkup:
    buttons = []
    for file in files:
        buttons.append([InlineKeyboardButton(text=file['name'], callback_data=f"file_{file['id']}")])
    buttons.append([InlineKeyboardButton(text=tb["menu_button"][language], callback_data="menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_menu_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=tb["menu_button"][language], callback_data="menu")]])
    return keyboard

def get_settings_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["set_token_button"][language], callback_data="settoken"),
            InlineKeyboardButton(text=tb["generate_token"][language], callback_data="generate_token")
        ],
        [InlineKeyboardButton(text=tb["menu_button"][language], callback_data="menu")]
    ])
    return keyboard

def get_file_action_keyboard(file_id: str, language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["download_button"][language], callback_data=f"download_{file_id}"),
            InlineKeyboardButton(text=tb["delete_button"][language], callback_data=f"delete_{file_id}")
        ],
        [InlineKeyboardButton(text=tb["menu_button"][language], callback_data="menu")]
    ])
    return keyboard
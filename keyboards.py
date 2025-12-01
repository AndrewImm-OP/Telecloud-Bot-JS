from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from translations import translations_buttons as tb
import math

def get_welcome_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["upload_button"].get(language, 'en'), callback_data="upload"),
            InlineKeyboardButton(text=tb["my_files_button"].get(language, 'en'), callback_data="myfiles")
        ],
        [
            InlineKeyboardButton(text=tb["settings_button"].get(language, 'en'), callback_data="settings")
        ]
    ])
    return keyboard

def get_files_keyboard(
    files: list,
    current_page: int = 1,
    language: str = "en"
) -> InlineKeyboardMarkup:
    buttons = []
    FILES_PER_PAGE = 5
    start_index = (current_page - 1) * FILES_PER_PAGE
    end_index = start_index + FILES_PER_PAGE

    files_on_page = files[start_index:end_index]

    for file in files_on_page:
        buttons.append([
            InlineKeyboardButton(
                text=file['name'],
                callback_data=f"file_{file['id']}"
            )
        ])

    pagination_buttons = []
    total_pages = math.ceil(len(files) / FILES_PER_PAGE)

    if current_page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=tb["previous_page_button"].get(language, 'en'),
                callback_data=f"page_{current_page - 1}"
            )
        )

    pagination_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages} 📄",
            callback_data="do_nothing"
        )
    )

    if current_page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=tb["next_page_button"].get(language, 'en'),
                callback_data=f"page_{current_page + 1}"
            )
        )
    
    buttons.append(pagination_buttons)

    buttons.append([InlineKeyboardButton(text=tb["menu_button"].get(language, 'en'), callback_data="menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_menu_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=tb["menu_button"].get(language, 'en'), callback_data="menu")]])
    return keyboard

def get_settings_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["set_token_button"].get(language, 'en'), callback_data="settoken"),
            InlineKeyboardButton(text=tb["generate_token"].get(language, 'en'), callback_data="generate_token")
        ],
        [InlineKeyboardButton(text=tb["menu_button"].get(language, 'en'), callback_data="menu")]
    ])
    return keyboard

def get_file_action_keyboard(file_id: str, language: str = "en") -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=tb["download_button"].get(language, 'en'), callback_data=f"download_{file_id}"),
            InlineKeyboardButton(text=tb["delete_button"].get(language, 'en'), callback_data=f"delete_{file_id}")
        ],
        [InlineKeyboardButton(text=tb["menu_button"].get(language, 'en'), callback_data="menu")]
    ])
    return keyboard
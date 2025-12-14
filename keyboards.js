import { Markup } from 'telegraf';
import { translationsButtons as tb } from './translations.js';

export function getWelcomeKeyboard(language = 'en') {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(tb.upload_button[language] || tb.upload_button.en, 'upload'),
      Markup.button.callback(tb.my_files_button[language] || tb.my_files_button.en, 'myfiles')
    ],
    [
      Markup.button.callback(tb.settings_button[language] || tb.settings_button.en, 'settings')
    ]
  ]);
}

export function getFilesKeyboard(files, currentPage = 1, language = 'en') {
  const buttons = [];
  const FILES_PER_PAGE = 5;
  const startIndex = (currentPage - 1) * FILES_PER_PAGE;
  const endIndex = startIndex + FILES_PER_PAGE;
  const filesOnPage = files.slice(startIndex, endIndex);

  for (const file of filesOnPage) {
    buttons.push([
      Markup.button.callback(file.name, `file_${file.id}`)
    ]);
  }

  const paginationButtons = [];
  const totalPages = Math.ceil(files.length / FILES_PER_PAGE);

  if (currentPage > 1) {
    paginationButtons.push(
      Markup.button.callback(tb.previous_page_button[language] || tb.previous_page_button.en, `page_${currentPage - 1}`)
    );
  }

  paginationButtons.push(
    Markup.button.callback(`📄 ${currentPage}/${totalPages} 📄`, 'do_nothing')
  );

  if (currentPage < totalPages) {
    paginationButtons.push(
      Markup.button.callback(tb.next_page_button[language] || tb.next_page_button.en, `page_${currentPage + 1}`)
    );
  }

  buttons.push(paginationButtons);
  buttons.push([Markup.button.callback(tb.menu_button[language] || tb.menu_button.en, 'menu')]);

  return Markup.inlineKeyboard(buttons);
}

export function getMenuKeyboard(language = 'en') {
  return Markup.inlineKeyboard([
    [Markup.button.callback(tb.menu_button[language] || tb.menu_button.en, 'menu')]
  ]);
}

export function getSettingsKeyboard(language = 'en') {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(tb.set_token_button[language] || tb.set_token_button.en, 'settoken'),
      Markup.button.callback(tb.generate_token[language] || tb.generate_token.en, 'generate_token')
    ],
    [Markup.button.callback(tb.menu_button[language] || tb.menu_button.en, 'menu')]
  ]);
}

export function getFileActionKeyboard(fileId, language = 'en') {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(tb.download_button[language] || tb.download_button.en, `download_${fileId}`),
      Markup.button.callback(tb.delete_button[language] || tb.delete_button.en, `delete_${fileId}`)
    ],
    [Markup.button.callback(tb.menu_button[language] || tb.menu_button.en, 'menu')]
  ]);
}


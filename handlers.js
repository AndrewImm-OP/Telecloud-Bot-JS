import { exec } from 'child_process';
import { promisify } from 'util';
import https from 'https';
import axios from 'axios';
import FormData from 'form-data';
import { User } from './db.js';
import { translationsMessages as tm } from './translations.js';
import { getFilesKeyboard, getFileActionKeyboard, getSettingsKeyboard, getMenuKeyboard } from './keyboards.js';
import fs from 'fs';
import path from 'path';
import { pipeline } from 'stream/promises';

const execAsync = promisify(exec);
const API_BASE_URL = 'https://cloud.onlysq.ru/api';
const UPLOAD_URL = 'https://cloud.onlysq.ru/upload'; 
const userStates = new Map();


const apiClient = axios.create({
  proxy: false,
  timeout: 60000,
  headers: {
    'User-Agent': 'TeleCloud-Bot-JS/1.0'
  }
});

function formatMessage(template, ...args) {
  let result = template;
  args.forEach((arg) => {
    result = result.replace('{}', arg);
  });
  return result;
}

export async function handleMyFiles(ctx) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.reply(tm.upload_no_token[language] || tm.upload_no_token.en);
  }

  await ctx.reply(tm.geting_files[language] || tm.geting_files.en);

  try {
    const curlCommand = `curl -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" "${API_BASE_URL}/files"`;
    
    const { stdout, stderr } = await execAsync(curlCommand, { timeout: 30000 });

    if (stderr && !stdout) {
      console.error('Curl stderr:', stderr);
    }

    let files;
    try {
      files = JSON.parse(stdout);
    } catch (e) {
      throw new Error('Invalid JSON response: ' + stdout);
    }

    if (!files || files.length === 0) {
      return ctx.reply(tm.no_files[language] || tm.no_files.en);
    }

    const keyboard = getFilesKeyboard(files, 1, language);
    await ctx.reply(tm.files[language] || tm.files.en, keyboard);
  } catch (error) {
    console.error('Error fetching files:', error.message);
    await ctx.reply(tm.file_list_failure[language] || tm.file_list_failure.en);
  }
}

export async function handleFileInfo(ctx, fileId) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.answerCbQuery();
  }

  try {
    const curlCommand = `curl -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" "${API_BASE_URL}/files"`;
    
    const { stdout } = await execAsync(curlCommand, { timeout: 30000 });
    
    let files;
    try {
      files = JSON.parse(stdout);
    } catch (e) {
      console.error('JSON parse error:', stdout);
      throw new Error('Invalid JSON');
    }

    const file = files.find(f => f.id === fileId);
    
    if (!file) {
      return ctx.answerCbQuery('File not found');
    }

    const message = formatMessage(
      tm.file_details[language] || tm.file_details.en,
      file.name,
      file.views,
      file.unique,
      `https://cloud.onlysq.ru/file/${file.id}`,
      `https://cloud.onlysq.ru/file/${file.id}?mode=dl`,
      `https://cloud.onlysq.ru/file/${file.id}?mode=view`
    );

    const keyboard = getFileActionKeyboard(fileId, language);
    
    try {
      await ctx.editMessageText(message, keyboard);
    } catch (e) {
      if (e.message.includes('message is not modified')) {
         await ctx.answerCbQuery();
         return;
      }
      await ctx.reply(message, keyboard);
    }
    
    await ctx.answerCbQuery();
  } catch (error) {
    console.error('Error getting file info:', error.message);
    await ctx.answerCbQuery('Error retrieving file info');
  }
}

export async function handleFileDownload(ctx, fileId) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.answerCbQuery();
  }

  await ctx.answerCbQuery();
  const statusMsg = await ctx.reply('⏳ Скачиваем файл...');

  try {
    const infoCommand = `curl -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" "${API_BASE_URL}/files"`;
    const { stdout: infoStdout } = await execAsync(infoCommand, { timeout: 30000 });
    const files = JSON.parse(infoStdout);
    const fileInfo = files.find(f => f.id === fileId);

    if (!fileInfo) {
      throw new Error('File info not found');
    }

    const fileName = fileInfo.name;
    const downloadUrl = `https://cloud.onlysq.ru/file/${fileId}?mode=dl`;
    const tempFilePath = path.join('./', fileName);

    console.log(`Скачиваем ${fileName}...`);
    
    await execAsync(`curl -L -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" -o "${tempFilePath}" "${downloadUrl}"`, { timeout: 300000 });

    if (fs.existsSync(tempFilePath)) {
      await ctx.replyWithDocument({ source: tempFilePath, filename: fileName });
      fs.unlinkSync(tempFilePath); // Удаляем после отправки
      await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
    } else {
      throw new Error('File not saved');
    }

  } catch (error) {
    console.error('Download error:', error.message);
    await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
    await ctx.reply(tm.file_download_failure[language] || tm.file_download_failure.en);
  }
}

export async function handleUpload(ctx) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.reply(tm.upload_no_token[language] || tm.upload_no_token.en);
  }

  userStates.set(ctx.from.id, 'awaiting_file');
  await ctx.reply(tm.upload_prompt[language] || tm.upload_prompt.en);
}

export async function handleFileUpload(ctx) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    userStates.delete(ctx.from.id);
    return ctx.reply(tm.upload_no_token[language] || tm.upload_no_token.en);
  }

  const statusMsg = await ctx.reply(tm.uploading_file[language] || tm.uploading_file.en);

  setImmediate(() => {
    uploadFileAsync(ctx, user.user_token, statusMsg.message_id, language).catch(error => {
      console.error('Async upload error:', error.message);
    });
  });

  userStates.delete(ctx.from.id);
}

async function uploadFileAsync(ctx, userToken, statusMessageId, language) {
  let tempFilePath = null;

  try {
    const fileData = ctx.message.document || ctx.message.video || ctx.message.audio || ctx.message.photo?.[ctx.message.photo.length - 1];
    if (!fileData) {
      await ctx.telegram.deleteMessage(ctx.chat.id, statusMessageId).catch(() => {});
      return ctx.reply(tm.upload_failure[language] || tm.upload_failure.en);
    }

    const fileLink = await ctx.telegram.getFileLink(fileData.file_id);
    
    const fileName = fileData.file_name || `file_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    tempFilePath = path.join('./', fileName); // В текущую папку
    
    const response = await axios.get(fileLink.href, { 
      responseType: 'stream',
      proxy: false
    });

    await pipeline(response.data, fs.createWriteStream(tempFilePath));

    console.log(`Файл скачан: ${tempFilePath}, начинаю загрузку через curl...`);

    const curlCommand = `curl -s -X POST -F "file=@${tempFilePath}" -b "user_token=${userToken}" -H "User-Agent: Mozilla/5.0" "${UPLOAD_URL}"`;
    
    const { stdout, stderr } = await execAsync(curlCommand, { timeout: 300000 });

    if (stderr && !stdout) {
      console.error('Curl stderr:', stderr);
      throw new Error('Curl error: ' + stderr);
    }

    console.log('Curl response:', stdout);

    let responseData;
    try {
      responseData = JSON.parse(stdout);
    } catch (e) {
      throw new Error('Invalid JSON from curl: ' + stdout);
    }

    if (fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }

    if (!responseData || !responseData.ok) {
      throw new Error('Upload failed: ' + JSON.stringify(responseData));
    }

    const fileId = responseData.url.split('/').pop();
    const message = formatMessage(
      tm.upload_success[language] || tm.upload_success.en,
      fileId,
      responseData.url,
      responseData.url + '?mode=dl',
      responseData.url + '?mode=view'
    );

    await ctx.telegram.deleteMessage(ctx.chat.id, statusMessageId).catch(() => {});
    await ctx.reply(message);

  } catch (error) {
    console.error('Upload error details:', error.message);
    
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      try { fs.unlinkSync(tempFilePath); } catch(e) {}
    }
    
    await ctx.telegram.deleteMessage(ctx.chat.id, statusMessageId).catch(() => {});
    await ctx.reply(tm.upload_failure[language] || tm.upload_failure.en);
  }
}

export async function handleSettings(ctx) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  const token = user?.user_token || 'Not set';
  const message = formatMessage(tm.settings_message[language] || tm.settings_message.en, token);
  const keyboard = getSettingsKeyboard(language);

  await ctx.reply(message, keyboard);
}

export async function handleSetToken(ctx) {
  const language = ctx.from.language_code || 'en';
  userStates.set(ctx.from.id, 'awaiting_token');
  await ctx.reply(tm.set_token_prompt[language] || tm.set_token_prompt.en);
}

export async function handleTokenInput(ctx, token) {
  const language = ctx.from.language_code || 'en';

  try {
    const response = await apiClient.get(`${API_BASE_URL}/files`, {
      headers: { Cookie: `user_token=${token}` }
    });

    if (response.status === 200) {
      await User.update(
        { user_token: token },
        { where: { telegram_id: ctx.from.id } }
      );
      userStates.delete(ctx.from.id);
      await ctx.reply(tm.token_set_success[language] || tm.token_set_success.en);
    }
  } catch (error) {
    console.error('Token validation error:', error.message);
    userStates.delete(ctx.from.id);
    await ctx.reply(tm.invalid_token[language] || tm.invalid_token.en);
  }
}

export async function handleGenerateToken(ctx) {
  const language = ctx.from.language_code || 'en';

  await ctx.answerCbQuery();
  const statusMsg = await ctx.reply('⏳ Генерируем токен...');

  setImmediate(async () => {
    try {
      const { stdout, stderr } = await execAsync(
        'curl -s -i https://cloud.onlysq.ru/ | grep -i "set-cookie:" | grep "user_token"',
        { timeout: 10000 }
      );

      if (stderr) {
        console.error('Curl stderr:', stderr);
      }

      console.log('Curl output:', stdout);

      const match = stdout.match(/user_token=([^;]+)/);
      
      if (!match) {
        throw new Error('Token not found in curl output');
      }

      const userToken = match[1];
      console.log('Generated token:', userToken);

      await User.update(
        { user_token: userToken },
        { where: { telegram_id: ctx.from.id } }
      );

      const message = formatMessage(
        tm.token_generated_success[language] || tm.token_generated_success.en,
        userToken
      );

      await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
      await ctx.reply(message);
    } catch (error) {
      console.error('Token generation error:', error.message);
      console.error('Error details:', error);
      
      await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
      await ctx.reply(tm.token_generated_failure[language] || tm.token_generated_failure.en);
    }
  });
}

export async function handleDeleteFile(ctx, fileId) {
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.answerCbQuery();
  }

  try {
    const infoCommand = `curl -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" "${API_BASE_URL}/files"`;
    const { stdout: infoStdout } = await execAsync(infoCommand, { timeout: 30000 });
    const files = JSON.parse(infoStdout);
    const fileInfo = files.find(f => f.id === fileId);

    if (!fileInfo || !fileInfo.owner_key) {
      return ctx.answerCbQuery('Owner key not found');
    }

    const deleteCommand = `curl -s -X DELETE -H "Authorization: ${fileInfo.owner_key}" -H "User-Agent: Mozilla/5.0" "https://cloud.onlysq.ru/file/${fileId}"`;
    
    const { stdout: deleteStdout } = await execAsync(deleteCommand, { timeout: 30000 });
    const response = JSON.parse(deleteStdout);

    if (response.ok) {
      await ctx.answerCbQuery();
      await ctx.editMessageText(tm.file_delete_success[language] || tm.file_delete_success.en, getMenuKeyboard(language));
    } else {
      throw new Error('Delete failed');
    }

  } catch (error) {
    console.error('Delete error:', error.message);
    await ctx.answerCbQuery();
    await ctx.reply(tm.file_delete_failure[language] || tm.file_delete_failure.en);
  }
}

export function getUserState(userId) {
  return userStates.get(userId);
}

export function clearUserState(userId) {
  userStates.delete(userId);
}


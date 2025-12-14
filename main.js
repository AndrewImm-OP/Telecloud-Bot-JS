import { Telegraf } from 'telegraf';
import dotenv from 'dotenv';
import { User, initDb, sequelize } from './db.js';
import { translationsMessages as tm } from './translations.js';
import { getWelcomeKeyboard, getFilesKeyboard } from './keyboards.js';
import * as handlers from './handlers.js';
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);

dotenv.config();

const TOKEN = process.env.TOKEN;
const LOCAL_TAPI = process.env.LOCAL_TAPI?.toLowerCase() === 'true';
const LOCAL_TAPI_URL = process.env.LOCAL_TAPI_URL || 'http://localhost:8081';

if (!TOKEN) {
  console.error('Отсутствует ТОКЕН в .env');
  process.exit(1);
}

const botOptions = {};
if (LOCAL_TAPI) {
  console.log(`Используем локальный TAPI на ${LOCAL_TAPI_URL}`);
  botOptions.telegram = {
    apiRoot: LOCAL_TAPI_URL,
    // !!!!!! При использовании TAPI, надо указать:
    webhookReply: false // выкл. авто-ответы через вебхук
  };
}

const bot = new Telegraf(TOKEN, botOptions);

bot.start(async (ctx) => {
  const language = ctx.from.language_code || 'en';
  
  const [user, created] = await User.findOrCreate({
    where: { telegram_id: ctx.from.id },
    defaults: {
      telegram_id: ctx.from.id,
      created_at: new Date(),
      user_token: null
    }
  });

  console.log(`Пользователь ${ctx.from.id} запустил бота на языке ${language}`);
  
  const markup = getWelcomeKeyboard(language);
  await ctx.reply(tm.start_message[language] || tm.start_message.en, markup);
});

bot.action('menu', async (ctx) => {
  const language = ctx.from.language_code || 'en';
  const markup = getWelcomeKeyboard(language);
  await ctx.editMessageText(tm.start_message[language] || tm.start_message.en, markup);
  await ctx.answerCbQuery();
});

bot.action('upload', async (ctx) => {
  await ctx.answerCbQuery();
  await handlers.handleUpload(ctx);
});

bot.action('myfiles', async (ctx) => {
  await ctx.answerCbQuery();
  await handlers.handleMyFiles(ctx);
});

bot.action('settings', async (ctx) => {
  await ctx.answerCbQuery();
  await handlers.handleSettings(ctx);
});

bot.action('settoken', async (ctx) => {
  await ctx.answerCbQuery();
  await handlers.handleSetToken(ctx);
});

bot.action('generate_token', async (ctx) => {
  await handlers.handleGenerateToken(ctx);
});

bot.action(/^page_(\d+)$/, async (ctx) => {
  const page = parseInt(ctx.match[1]);
  const language = ctx.from.language_code || 'en';
  const user = await User.findOne({ where: { telegram_id: ctx.from.id } });

  if (!user || !user.user_token) {
    return ctx.answerCbQuery();
  }

  try {
    const curlCommand = `curl -s -b "user_token=${user.user_token}" -H "User-Agent: Mozilla/5.0" "https://cloud.onlysq.ru/api/files"`;
    const { stdout } = await execAsync(curlCommand, { timeout: 30000 });
    const files = JSON.parse(stdout);

    const keyboard = getFilesKeyboard(files, page, language);
    await ctx.editMessageReplyMarkup(keyboard.reply_markup);
    await ctx.answerCbQuery();
  } catch (error) {
    console.error('Pagination error:', error.message);
    await ctx.answerCbQuery('Error');
  }
});

bot.action(/^file_(.+)$/, async (ctx) => {
  const fileId = ctx.match[1];
  await handlers.handleFileInfo(ctx, fileId);
});

bot.action(/^delete_(.+)$/, async (ctx) => {
  const fileId = ctx.match[1];
  await handlers.handleDeleteFile(ctx, fileId);
});

bot.action(/^download_(.+)$/, async (ctx) => {
  const fileId = ctx.match[1];
  await handlers.handleFileDownload(ctx, fileId);
});

bot.action('do_nothing', async (ctx) => {
  await ctx.answerCbQuery();
});

bot.on('text', async (ctx) => {
  const userState = handlers.getUserState(ctx.from.id);

  if (userState === 'awaiting_token') {
    await handlers.handleTokenInput(ctx, ctx.message.text);
  }
});

bot.on(['document', 'video', 'audio', 'photo'], async (ctx) => {
  const userState = handlers.getUserState(ctx.from.id);

  if (userState === 'awaiting_file') {
    await handlers.handleFileUpload(ctx);
  }
});

bot.catch((err, ctx) => {
  console.error(`Error for ${ctx.updateType}:`, err);
});

process.once('SIGINT', () => {
  console.log('Bot is shutting down...');
  bot.stop('SIGINT');
  sequelize.close();
});

process.once('SIGTERM', () => {
  console.log('Bot is shutting down...');
  bot.stop('SIGTERM');
  sequelize.close();
});

async function main() {
  try {
    await initDb();
    console.log('Бот запущен.');
    await bot.launch();
    console.log('Listening for updates...');
  } catch (error) {
    console.error('Ошибка запуска:', error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Критическая ошибка:', error);
  process.exit(1);
});

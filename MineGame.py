import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()
TOKEN = "7896226554:AAFCqliOMNxOp-vNXtTNpMqAaybD7bIYOHg"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

BOARD_SIZE = 5
MINE = "💣"
NUMBERS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
HIDDEN = "■"

games = {}

def generate_board(num_mines):
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    mines = set()
    while len(mines) < num_mines:
        x, y = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
        if (x, y) not in mines:
            mines.add((x, y))
            board[y][x] = -1
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if board[y][x] == -1:
                continue
            count = sum((nx, ny) in mines for nx in range(x - 1, x + 2) for ny in range(y - 1, y + 2) if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE)
            board[y][x] = count
    return board, [[HIDDEN for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)], mines

def create_board_markup(visible_board):
    markup = InlineKeyboardMarkup(row_width=BOARD_SIZE)
    for y in range(BOARD_SIZE):
        row_buttons = [
            InlineKeyboardButton(
                text=visible_board[y][x],
                callback_data=f"open:{x}:{y}"
            ) for x in range(BOARD_SIZE)
        ]
        markup.add(*row_buttons)
    return markup

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🎮 Играть"))
    return markup

def mines_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💥 5 бомб", callback_data="mines:5"))
    markup.add(InlineKeyboardButton("💥 10 бомб", callback_data="mines:10"))
    markup.add(InlineKeyboardButton("💥 15 бомб", callback_data="mines:15"))
    return markup

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это бот для игры в «Мины». Нажми «Играть», чтобы начать. Разработчик: @OneDayBruh!", reply_markup=main_menu())

@dp.message_handler(lambda message: message.text == "🎮 Играть")
async def choose_mines(message: types.Message):
    await message.answer("Выберите количество бомб на поле:", reply_markup=mines_menu())

@dp.callback_query_handler(lambda call: call.data.startswith("mines:"))
async def start_game(call: types.CallbackQuery):
    num_mines = int(call.data.split(":")[1])
    chat_id = call.message.chat.id

    games[chat_id] = {"data": generate_board(num_mines), "message_id": None}
    board_view = games[chat_id]["data"][1]
    markup = create_board_markup(board_view)

    sent_message = await call.message.answer(f"🎮 Игра началась! Бомб на поле: {num_mines}", reply_markup=markup)
    games[chat_id]["message_id"] = sent_message.message_id
    await call.message.delete()

@dp.callback_query_handler(lambda call: call.data.startswith("open:"))
async def open_cell(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    if chat_id not in games:
        return
    
    _, x, y = call.data.split(":")
    x, y = int(x), int(y)

    board, visible_board, mines = games[chat_id]["data"]

    if visible_board[y][x] != HIDDEN:
        await call.answer("Эта клетка уже открыта!", show_alert=True)
        return

    if (x, y) in mines:
        visible_board[y][x] = MINE
        await call.message.answer("💥 Бум! Вы проиграли, не сдавайтесь и все будет бомбически!", reply_markup=main_menu())
        await bot.delete_message(chat_id, games[chat_id]["message_id"])
        del games[chat_id]
        return

    visible_board[y][x] = NUMBERS[board[y][x]]
    markup = create_board_markup(visible_board)
    await call.message.edit_reply_markup(reply_markup=markup)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

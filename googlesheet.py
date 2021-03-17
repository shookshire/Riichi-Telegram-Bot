import gspread
import string
from threading import Thread, Lock
from config import SPREADSHEET_CONFIG, MAIN_ADMIN
from log_helper import logger

mutex = Lock()


def can_convert_to_int(str):
  try:
    int(str)
    return True
  except:
    return False


class Googlesheets:
  max_attempt = 5

  def __init__(self):
    gc = gspread.service_account(
        filename="./service_account.json")
    self.connection = gc.open_by_key(SPREADSHEET_CONFIG['sheet_key'])

  def get_player_list(self):
    players = self.connection.worksheet('players')
    res = players.get('A2:C')
    filteredWithTelegramId = list(
        filter(lambda x: len(x) == 3 and can_convert_to_int(x[2]), res))
    return list(map(lambda x: {'pid': int(x[0]), 'name': string.capwords(x[1].strip()), 'telegram_id': int(x[2])}, filteredWithTelegramId))

  def get_venue_list(self):
    venue = self.connection.worksheet('venue')
    res = venue.get('A2:C')
    filtered = list(filter(lambda x: len(x) == 3 and int(x[2]), res))
    return list(map(lambda x: {'vid': int(x[0]), 'name': x[1]}, filtered))

  def get_mode_list(self):
    mode = self.connection.worksheet('mode')
    res = mode.get('A2:D')
    filtered = list(filter(lambda x: len(x) == 4 and int(x[3]), res))
    return list(map(lambda x: {'mid': int(x[0]), 'name': x[2], 'vid': int(x[1])}, filtered))

  def get_last_id(self, sheet_name):
    worksheet = self.connection.worksheet(sheet_name)
    row_count = worksheet.row_count
    return int(worksheet.acell('A{}'.format(row_count)).value)

  def initialize(self):
    mutex.acquire()
    self.gid = self.get_last_id('game_info')
    self.hid = self.get_last_id('hand_info')
    self.ihid = self.get_last_id('hand_result')

  def release(self):
    mutex.release()

  def get_gid(self):
    self.gid += 1
    return self.gid

  def get_hid(self):
    self.hid += 1
    return self.hid

  def get_ihid(self):
    self.ihid += 1
    return self.ihid

  def append_row_to_sheet(self, worksheet, data):
    for i in range(0, self.max_attempt):
      try:
        worksheet.append_row(data, value_input_option='USER_ENTERED')
        break
      except Exception as e:
        logger.error(e)
        if i == self.max_attempt - 1:
          raise

  def set_game_info(self, data):
    worksheet = self.connection.worksheet('game_info')
    gid = self.get_gid()

    data.insert(0, gid)
    self.append_row_to_sheet(worksheet, data)
    return gid

  def set_game_result(self, data):
    worksheet = self.connection.worksheet('game_result')
    self.append_row_to_sheet(worksheet, data)

  def set_hand_info(self, data):
    worksheet = self.connection.worksheet('hand_info')
    hid = self.get_hid()

    data.insert(0, hid)
    self.append_row_to_sheet(worksheet, data)
    return hid

  def set_hand_result(self, data):
    worksheet = self.connection.worksheet('hand_result')
    ihid = self.get_ihid()

    data.insert(0, ihid)
    self.append_row_to_sheet(worksheet, data)

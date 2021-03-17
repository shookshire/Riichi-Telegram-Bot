class Location:

  def __init__(self, venue_list, mode_list):
    self.venue = None
    self.mode = None

    self.venue_list = venue_list
    self.mode_list = mode_list

  def set_venue(self, name):
    venue = list(filter(lambda x: x['name'] == name, self.venue_list))
    if not venue:
      return False, 'invalid'
    self.venue = venue[0]
    return True, None

  def set_mode(self, name):
    mode = list(filter(lambda x: (
        x['name'] == name and x['vid'] == self.get_venue_id()), self.mode_list))

    if not mode:
      return False, 'invalid'
    self.mode = mode[0]
    return True, None

  def get_valid_mode(self):
    return list(filter(lambda x: x['vid'] == self.venue['vid'], self.mode_list))

  def get_venue_id(self):
    return self.venue['vid'] if not self.venue is None else None

  def get_mode_id(self):
    return self.mode['mid'] if not self.mode is None else None

  def get_venue_name(self):
    return self.venue['name'] if not self.venue is None else None

  def get_mode_name(self):
    return self.mode['name'] if not self.mode is None else None

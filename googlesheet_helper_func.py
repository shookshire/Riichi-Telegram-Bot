def check_valid_name_from_list(name, player_list):
	filtered = list(filter(lambda x: x['name'] == name, player_list))
	return filtered[0] if len(filtered) else None

def check_valid_id_from_list(pid, player_list):
	filtered = list(filter(lambda x: x['pid'] == pid, player_list))
	return filtered[0] if len(filtered) else None

def filter_mode_by_bid(mode_list, vid):
	return list(filter(lambda x: x['vid'] == vid, mode_list))
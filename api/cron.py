# -*- coding: utf-8 -*-
from robot import get_room_table
from api.models import Room

def save_room_table():
	# clear all room data
	Room.objects.all().delete()
	for date in range(0, 7):
		result_dict = get_room_table(date)
		for room, time_table in result_dict.items():
			binary_str = ''
			for availbility in time_table:
				binary_str += str(availbility)
			availbility_str = int(binary_str, 2) # 2 -> 10
			room_obj = Room(date=date, room=room, availability=availbility_str)
			room_obj.save()
	print "room table update success."
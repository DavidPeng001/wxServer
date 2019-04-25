# -*- coding: utf-8 -*-
from robot import get_room_table
from api.models import Room

def save_room_table():
	# clear all room data
	results = []
	for date in range(0, 7):
		result_dict = get_room_table(date)
		for room, time_table in result_dict.items():
			binary_str = ''
			for availability in time_table:
				binary_str += str(availability)
			availability_str = int(binary_str, 2) # bin -> dec
			results.append(dict(date=date, room=room, availability=availability_str))

	Room.objects.all().delete()
	for result in results:
		room_obj = Room(date=result['date'], room=result['room'], availability=result['availability'])
		room_obj.save()
	print "room table update success."
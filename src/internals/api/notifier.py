
import logging
from typing import Callable

from internals.notify.notfiable import Notifiable, NotifiableController
from internals.enums.enum import InternalTypes

class Reminder(Notifiable):
    def __init__(self, notif: Notifiable, DEFAULT=None) -> None:
        super().__init__(notif.data, notif.id, notif.call_date, notif.has_temp_id)
        data_dict: dict = notif.data
        del self.data
        del self.type
        self.date_created = data_dict.get(InternalTypes.REMINDERS_DATE_CREATED_FIELD.value, DEFAULT)
        self.content = data_dict.get(InternalTypes.REMINDERS_CONTENT_FIELD.value, DEFAULT)
        self.user_id = data_dict.get(InternalTypes.USER_ID.value, DEFAULT)
        self.scope = data_dict.get(InternalTypes.REMINDERS_SCOPE_FIELD.value, DEFAULT)
        self.guild_id =  data_dict.get(InternalTypes.GUILD_ID.value, DEFAULT)
        self.channel_id = data_dict.get(InternalTypes.CHANNEL_ID.value, DEFAULT)
        
    def fromRaw(data:dict, DEFAULT=None):        
        """<data_dict>: {col:val,...}"""
        # logging.debug(f"1 fromRaw: {data} {type(data)}")
        id = data.get(InternalTypes.ID.value, DEFAULT)
        temp_id = data.get(InternalTypes.REMINDERS_CACHE_ID_FIELD.value, DEFAULT)
        is_temp_id = temp_id and not id
        # logging.debug(f"reminder fromRaw: temp: {temp_id} id: {id} istemp: {is_temp_id}")
        if is_temp_id:
            id = temp_id

        reminder = Reminder(Notifiable(data,
                                       has_temp_id=is_temp_id,
                                       id=id,
                                       call_date=data.get(InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value, DEFAULT)
                                       ))
        # logging.debug(f"end of reminder fromRaw: temp: {temp_id} id: {id} istemp: {reminder.has_temp_id}")
        return reminder
class Notifier():
    def __init__(self, controller: NotifiableController) -> None:
        self.controller = controller
        self.controller.subscribe(self.notifyListeners)
        self.hooks = []

    def subscribeListener(self, function: Callable[..., None]):
        self.hooks.append(function)

    


    def notifyListeners(self, notif: Notifiable):
        obj = notif
        if notif.type == InternalTypes.REMINDERS:
            obj = Reminder(obj)
                     
        for hook in self.hooks:
            hook(obj)
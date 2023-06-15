
from typing import Callable

from internals.notify.notfiable import Notifiable, NotifiableController
from internals.enums.enum import InternalTypes

class Reminder(Notifiable):
    def __init__(self, notif: Notifiable, DEFAULT=None) -> None:
        super().__init__(notif.data, notif.id, notif.call_date)
        data_dict: dict = notif.data
        del self.data
        del self.type
        self.date_created = data_dict.get(InternalTypes.REMINDERS_DATE_CREATED_FIELD.value, DEFAULT)
        self.content = data_dict.get(InternalTypes.REMINDERS_CONTENT_FIELD.value, DEFAULT)
        self.user_id = data_dict.get(InternalTypes.USER_ID.value, DEFAULT)
        self.scope = data_dict.get(InternalTypes.REMINDERS_SCOPE_FIELD.value, DEFAULT)
        self.guild_id =  data_dict.get(InternalTypes.GUILD_ID.value, DEFAULT)
        self.channel_id = data_dict.get(InternalTypes.CHANNEL_ID.value, DEFAULT)
        
    def fromRaw(data_dict:dict, DEFAULT=None):        
        """<data_dict>: {col:val,...}"""
        reminder = Reminder(Notifiable(None,None,None))
        reminder.id = data_dict.get(InternalTypes.ID.value, DEFAULT)
        reminder.user_id = data_dict.get(InternalTypes.USER_ID.value, DEFAULT)
        reminder.call_date = data_dict.get(InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value, DEFAULT)
        reminder.date_created = data_dict.get(InternalTypes.REMINDERS_DATE_CREATED_FIELD.value, DEFAULT)
        reminder.content = data_dict.get(InternalTypes.REMINDERS_CONTENT_FIELD.value, DEFAULT)
        reminder.scope = data_dict.get(InternalTypes.REMINDERS_SCOPE_FIELD.value, DEFAULT)
        reminder.guild_id =  data_dict.get(InternalTypes.GUILD_ID.value, DEFAULT)
        reminder.channel_id = data_dict.get(InternalTypes.CHANNEL_ID.value, DEFAULT)

        return reminder
class Notifier():
    def __init__(self, controller: NotifiableController) -> None:
        self.controller = controller
        self.hooks = []
    def subscribeListener(self, function: Callable[..., None]):
        self.hooks.append(function)

    def notifyListeners(self, notif: Notifiable):
        obj = notif
        if notif.type == InternalTypes.REMINDERS:
            obj = Reminder(obj)
                     
        for hook in self.hooks:
            hook(obj)
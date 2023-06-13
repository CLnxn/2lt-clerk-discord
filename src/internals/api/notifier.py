
from typing import Callable

from internals.notify.notfiable import Notifiable, NotifiableController
from internals.enums.enum import InternalTypes

class Reminder(Notifiable):
    def __init__(self, notif: Notifiable) -> None:
        super().__init__(notif.data, notif.id, notif.call_date)
        data = notif.data
        del self.data
        del self.type
        self.date_created = data[InternalTypes.REMINDERS_DATE_CREATED_FIELD.value]
        self.content = data[InternalTypes.REMINDERS_CONTENT_FIELD.value]
        self.user_id = data[InternalTypes.USER_ID.value]
        self.scope = data[InternalTypes.REMINDERS_SCOPE_FIELD.value]
        if InternalTypes.GUILD_ID.value in data:
            self.guild_id =  data[InternalTypes.GUILD_ID.value]
        
        if InternalTypes.CHANNEL_ID.value in data:
            self.channel_id = data[InternalTypes.CHANNEL_ID.value]
    def fromRaw(data_dict:dict):        
        """<data_dict>: {col:val,...}"""
        reminder = Reminder(Notifiable(None,None,None))
        reminder.id = data_dict[InternalTypes.ID.value]
        reminder.call_date = data_dict[InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value]
        reminder.date_created = data_dict[InternalTypes.REMINDERS_DATE_CREATED_FIELD.value]
        reminder.content = data_dict[InternalTypes.REMINDERS_CONTENT_FIELD.value]
        if InternalTypes.GUILD_ID.value in data_dict:
            reminder.guild_id =  data_dict[InternalTypes.GUILD_ID.value]
        
        if InternalTypes.CHANNEL_ID.value in data_dict:
            reminder.channel_id = data_dict[InternalTypes.CHANNEL_ID.value]

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
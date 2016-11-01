import psycopg2 as dbapi2
import init_database


class Message:
    def __init__(self, senderID, room, text):
        self.id = None
        self.senderID = senderID
        self.room = room
        self.text = text

    def save(self):
        if self.id is not None:  # if id is not none it has been in db already
            return
        with dbapi2.connect(init_database.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(""" INSERT INTO MESSAGE (ID, TEXT, RoomID, SenderID)
                                             VALUES ( DEFAULT, %(text)s, %(RoomID)s, %(SenderID)s ) RETURNING ID""",
                               {'text': self.text, 'RoomID': self.room.id, 'SenderID': self.senderID})

                self.id = cursor.fetchone()[0]

                for participant in self.room.participants:
                    cursor.execute(""" INSERT INTO MESSAGE_STATUS (MessageID, ReceiverID)
                                          VALUES ( %(MessageID)s, %(ReceiverID)s )""",
                                   {'MessageID': self.id, 'ReceiverID': participant})

    @staticmethod
    def get_messages(room):
        messages = []
        with dbapi2.connect(init_database.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(""" SELECT * FROM MESSAGE WHERE MESSAGE.RoomID=%(RoomID)s""",
                               {'RoomID': room.id})
                result = cursor.fetchall()

                for res in result:
                    msg = Message(res[4], room, res[1])
                    msg.id = res[0]
                    msg.date = res[2]
                    messages.append(msg)

        return messages


class Room:
    def __init__(self, name=None, participants=None):
        self.id = None
        self.name = name
        self.participants = [] if participants is None else participants

    def save(self):
        if self.id is not None:  # if id is not none it has been in db already
            return

        with dbapi2.connect(init_database.dsn) as connection:
            with connection.cursor() as cursor:
                # first create room entry
                cursor.execute(""" INSERT INTO MESSAGE_ROOM (ID, NAME)
                                      VALUES ( DEFAULT, %(name)s ) RETURNING ID""",
                               {'name': self.name})

                self.id = cursor.fetchone()[0]

                # and create participant entry for each participant and roomID
                for participant in self.participants:
                    cursor.execute(""" INSERT INTO MESSAGE_PARTICIPANT (RoomID, UserID)
                                          VALUES ( %(RoomID)s, %(UserID)s )""",
                                   {'RoomID': self.id, 'UserID': participant})

    @staticmethod
    def get_room_headers(userID):
        """ Load All Room Headers of User participated"""
        rooms = []
        with dbapi2.connect(init_database.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(""" SELECT RoomID, NAME FROM MESSAGE_ROOM LEFT JOIN MESSAGE_PARTICIPANT
                                        ON MESSAGE_ROOM.ID=MESSAGE_PARTICIPANT.RoomID
                                        WHERE MESSAGE_PARTICIPANT.UserID=%(UserID)s""",
                               {'UserID': userID})
                result = cursor.fetchall()

                for res in result:
                    room = Room(name=res[1])  # todo if name is null -> add first 3 participants name?
                    room.id = res[0]
                    rooms.append(room)

        return rooms
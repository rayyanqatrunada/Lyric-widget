import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, Message, MessageType

MPRIS_PREFIX = "org.mpris.MediaPlayer2."

async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    reply = await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="ListNames",
        )
    )

    if not reply or not reply.body:
        print("Gagal mengambil daftar nama D-Bus.")
        return

    names = reply.body[0]
    players = sorted(
        name for name in names
        if name.startswith(MPRIS_PREFIX)
    )

    print("=== Lyric Widget: MPRIS Monitor ===")
    print("Player terdeteksi:", players or "Tidak ada")
    print("Menunggu perubahan status...\n")

    def on_message(message):
        if message.message_type != MessageType.SIGNAL:
            return

        if message.interface == "org.freedesktop.DBus" and (
            message.member == "NameOwnerChanged"
        ):
            name, old_owner, new_owner = message.body
            if name.startswith(MPRIS_PREFIX):
                if new_owner and not old_owner:
                    print(f"[PLAYER DIBUKA] {name}", flush=True)
                elif old_owner and not new_owner:
                    print(f"[PLAYER DITUTUP] {name}", flush=True)

        elif message.interface == "org.freedesktop.DBus.Properties" and (
            message.member == "PropertiesChanged"
        ):
            interface, changed, _invalidated = message.body
            if interface != "org.mpris.MediaPlayer2.Player":
                return

            status = changed.get("PlaybackStatus")
            if status:
                print(
                    f"[STATUS] {message.sender}: {status.value}",
                    flush=True,
                )

            metadata = changed.get("Metadata")
            if metadata:
                title = metadata.value.get("xesam:title")
                artist = metadata.value.get("xesam:artist")
                if title:
                    artists = artist.value if artist else []
                    print(
                        f"[LAGU] {title.value} — "
                        f"{', '.join(artists)}",
                        flush=True,
                    )

    bus.add_message_handler(on_message)

    await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="AddMatch",
            signature="s",
            body=[
                "type='signal',"
                "interface='org.freedesktop.DBus',"
                "member='NameOwnerChanged'"
            ],
        )
    )

    await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="AddMatch",
            signature="s",
            body=[
                "type='signal',"
                "interface='org.freedesktop.DBus.Properties',"
                "member='PropertiesChanged',"
                "path='/org/mpris/MediaPlayer2'"
            ],
        )
    )

    await asyncio.Event().wait()

asyncio.run(main())

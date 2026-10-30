import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, Message

MPRIS_PREFIX = "org.mpris.MediaPlayer2."
PLAYER_PATH = "/org/mpris/MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


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

    players = sorted(
        name for name in reply.body[0]
        if name.startswith(MPRIS_PREFIX)
    )

    if not players:
        print("Tidak ada player MPRIS yang terdeteksi.")
        return

    # Prioritaskan Strawberry jika sedang berjalan.
    player = next(
        (name for name in players if "strawberry" in name.lower()),
        players[0],
    )

    print(f"Player: {player}")
    print("Tekan Ctrl+C untuk berhenti.\n")

    async def get_property(name):
        reply = await bus.call(
            Message(
                destination=player,
                path=PLAYER_PATH,
                interface=PROPERTIES_INTERFACE,
                member="Get",
                signature="ss",
                body=[PLAYER_INTERFACE, name],
            )
        )
        if not reply or not reply.body:
            raise RuntimeError(f"Gagal membaca properti {name}")
        return reply.body[0].value

    try:
        while True:
            status = await get_property("PlaybackStatus")
            position = await get_property("Position")

            seconds = position / 1_000_000
            minutes, seconds = divmod(seconds, 60)

            print(
                f"\rStatus: {status:<8} | "
                f"Posisi: {int(minutes):02d}:{seconds:05.2f}",
                end="",
                flush=True,
            )

            await asyncio.sleep(0.25)

    except KeyboardInterrupt:
        print("\nPengujian dihentikan.")
    except Exception as error:
        print(f"\nGagal membaca player: {error}")
    finally:
        bus.disconnect()


asyncio.run(main())

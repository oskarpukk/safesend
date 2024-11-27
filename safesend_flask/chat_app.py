from uuid import uuid4
from nicegui import ui
import socket
from typing import Dict, List, Tuple

# Store chat messages as (user_id, avatar_url, message_text)
messages: List[Tuple[str, str, str]] = []
# Store connected clients
connected_users: Dict[str, dict] = {}

def get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

@ui.page('/')
def index() -> None:
    """Main chat interface setup."""
    async def send() -> None:
        if text.value:
            messages.append((user, avatar, text.value))
            await chat_messages.refresh()
            text.value = ''

    # Generate unique user identifier and avatar
    user = str(uuid4())
    avatar = f'https://robohash.org/{user}?bgset=bg2'
    
    connected_users[user] = {
        'avatar': avatar
    }

    with ui.column().classes('w-full items-stretch'):
        chat_messages(user)

    with ui.footer().classes('bg-white'):
        with ui.row().classes('w-full items-center'):
            with ui.avatar():
                ui.image(avatar)
            text = ui.input(placeholder='message') \
                .props('rounded outlined') \
                .classes('flex-grow') \
                .on('keydown.enter', send)

    ui.label(f'Connected as: {user}')
    ui.label(f'Server IP: {get_local_ip()}')

@ui.refreshable
def chat_messages(own_id: str) -> None:
    """Display chat messages."""
    for user_id, avatar, text in messages:
        ui.chat_message(
            avatar=avatar,
            text=text,
            sent=user_id == own_id
        )

def main() -> None:
    """Initialize and run the chat application."""
    server_ip = get_local_ip()
    print(f"Starting server on: http://{server_ip}:8080")
    
    ui.run(
        host=server_ip,
        port=8080,
        title="SafeSend Network Chat"
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()
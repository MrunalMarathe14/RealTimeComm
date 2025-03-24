import asyncio
import threading
import websockets
import tkinter as tk
from tkinter import simpledialog, scrolledtext

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Chat")

        # Input for Server IP
        self.server_ip = simpledialog.askstring("Server IP", "Enter Server IP Address:", initialvalue="127.0.0.1")
        self.server_port = 8765  # Default port

        # Input for Client Name
        self.client_name = simpledialog.askstring("Client Name", "Enter your name:")

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
        self.chat_area.pack(padx=10, pady=10)
        self.chat_area.config(state=tk.DISABLED)

        # Message entry box
        self.message_entry = tk.Entry(root, width=40)
        self.message_entry.pack(padx=10, pady=5)

        # Send button
        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack(pady=5)

        self.websocket = None
        self.loop = asyncio.new_event_loop()

        # Run asyncio event loop in a separate thread
        threading.Thread(target=self.run_asyncio_loop, daemon=True).start()

    def run_asyncio_loop(self):
        """Runs the asyncio event loop in a background thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(f"ws://{self.server_ip}:{self.server_port}")
            await self.websocket.send(self.client_name)  # Send client name to server
            await self.receive_messages()  # Start receiving messages
        except Exception as e:
            self.update_chat(f"Error: {e}")

    async def receive_messages(self):
        """Receive messages from the server asynchronously."""
        try:
            async for message in self.websocket:
                self.root.after(0, self.update_chat, message)  # Update chat in Tkinter
        except Exception as e:
            self.root.after(0, self.update_chat, f"Disconnected: {e}")

    def send_message(self):
        """Send a message to the server and retain it in the chat window."""
        message = self.message_entry.get().strip()
        if self.websocket and message:
            formatted_message = f"You: {message}"
            self.update_chat(formatted_message)  # Show sent message
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self.loop)
            self.message_entry.delete(0, tk.END)

    def update_chat(self, message):
        """Update the chat window with new messages."""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()

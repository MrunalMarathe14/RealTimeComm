import asyncio
import websockets
import tkinter as tk
from threading import Thread

# Store connected clients with names
clients = {}

class ChatServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Chat Application")

        # Chat history display
        self.text_area = tk.Text(root, height=20, width=50)
        self.text_area.pack(pady=10)
        self.text_area.config(state=tk.DISABLED)

        # Dropdown to select client
        self.client_var = tk.StringVar()
        self.client_var.set("All Clients")  # Default: Broadcast
        self.client_dropdown = tk.OptionMenu(root, self.client_var, "All Clients")
        self.client_dropdown.pack()

        # Message input field
        self.entry = tk.Entry(root, width=40)
        self.entry.pack(pady=5)

        # Send button
        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack()

        # Start WebSocket server in a separate thread
        Thread(target=asyncio.run, args=(self.start_server(),), daemon=True).start()

    async def start_server(self):
        server = await websockets.serve(self.handle_client, "0.0.0.0", 8765)
        self.update_text_area("Server started. Waiting for connections...\n")
        await server.wait_closed()

    async def handle_client(self, websocket, path):
        # Get client name from the first message
        client_name = await websocket.recv()
        clients[client_name] = websocket
        self.update_dropdown()
        self.update_text_area(f"{client_name} connected.\n")

        try:
            async for message in websocket:
                self.update_text_area(f"\n{client_name}: {message}\n")
                # Server does not forward messages to other clients!
        except websockets.exceptions.ConnectionClosed:
            self.update_text_area(f"{client_name} disconnected.\n")
        finally:
            del clients[client_name]
            self.update_dropdown()

    async def send_to_client(self, name, message):
        client = clients.get(name)
        if client:
            await client.send(f"Server: {message}")

    async def broadcast(self, message):
        for client in clients.values():
            await client.send(f"Server: {message}")

    def send_message(self):
        message = self.entry.get()
        self.entry.delete(0, tk.END)
        selected_client = self.client_var.get()

        if message:
            self.update_text_area(f"\nYou (Server): {message}\n")

            if selected_client == "All Clients":
                asyncio.run(self.broadcast(message))
            else:
                asyncio.run(self.send_to_client(selected_client, message))

    def update_text_area(self, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message)
        self.text_area.config(state=tk.DISABLED)

    def update_dropdown(self):
        menu = self.client_dropdown["menu"]
        menu.delete(0, "end")
        menu.add_command(label="All Clients", command=lambda: self.client_var.set("All Clients"))
        for name in clients.keys():
            menu.add_command(label=name, command=lambda n=name: self.client_var.set(n))

# Run the GUI
root = tk.Tk()
server = ChatServer(root)
root.mainloop()

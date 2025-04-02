from tkinter import *

root = Tk()
root.title('Search')
root.geometry("500x300")

# Create a frame to hold all content
frame = Frame(root)
frame.place(relx=0.5, rely=0.5, anchor=CENTER)

# Update the listbox
def update(data):
    # Clear the listbox
    my_list.delete(0, END)

    # Add items to listbox
    for item in data:
        my_list.insert(END, item)

# Update entry box with listbox clicked
def fillout(e):
    # Delete whatever is in the entry box
    my_entry.delete(0, END)

    # Add clicked list item to entry box
    my_entry.insert(0, my_list.get(ANCHOR))

# Create function to check entry vs listbox
def check(e):
    # Grab what was typed
    typed = my_entry.get()

    if typed == '':
        data = channel_list
    else:
        data = []
        for item in channel_list:
            if typed.lower() in item.lower():
                data.append(item)

    # Update the listbox with selected items
    update(data)

# Create function for the Join button
def join():
    result = my_entry.get()
    print(f"You joined: {result}")  # Example action, you can replace it with your desired functionality

# Create a label inside the frame
my_label = Label(frame, text="Search new channel",
    font=("Arial", 20))
my_label.pack(pady=10)

# Create a horizontal frame for the entry and button
input_frame = Frame(frame)
input_frame.pack(pady=(10,0))

# Create an entry box inside the input_frame
my_entry = Entry(input_frame, width=43)
my_entry.pack(side=LEFT, padx=5)

# Create the Join button inside the input_frame
join_button = Button(input_frame, text="Join", command=join)
join_button.pack(side=LEFT, padx=5)

# Create a listbox inside the frame
my_list = Listbox(frame, width=50, height=5) 
my_list.pack(pady=5)

# Create a list of items
channel_list = ["Pepperoni", "Peppers", "Mushrooms",
    "Cheese", "Onions", "Ham", "Taco"]

# Add the items to the listbox
update(channel_list)

# Create a binding on the listbox onclick
my_list.bind("<ButtonRelease-1>", fillout)

# Create a binding on the entry box
my_entry.bind("<KeyRelease>", check)

root.mainloop()
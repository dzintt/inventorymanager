# Inventory Manager
Discord bot integrated with Google Sheets made for people who have somebody else managing their shoe inventory to keep everything nice and organized!

# Setup


# Commands

**add** (tracking number) (size) (item name)
- Adds the item into the Google Sheet

**remove** (tracking number)
- Removes the item from the Google Sheet

**inventory** (active/sold/completed)
- View your inventory for the specified section

**sell** (inventory index) *requires a .pdf file shipping label attached with your command message*
- Marks the item as sold and pending for shipment

**unsell** (inventory index)
- Unmarks the item as sold and pending for shipment

## Owner Commands

**toship**
- View all the items that are pending shipment

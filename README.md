# Inventory Manager
Discord bot integrated with Google Sheets made for people who have somebody else managing their shoe inventory to keep everything nice and organized!

# Google Sheets Setup
1. Make a copy of this Google Sheet: https://docs.google.com/spreadsheets/d/1tT0zwWYl32oauIu20bPLReQgW_MsG2UHgK80hfpixXM/edit?usp=sharing
2. Create a new project at https://console.cloud.google.com/apis/dashboard
3. Enable the Google Sheets API at https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com
4. Create service account credentials (make sure it has project editor permissions)
5. Create your key in JSON format and a file called "credentials.json" should be downloaded
6. Replace the empty credentials.json in the code folder with your new one you just downloaded
7. Go inside the credentials.json file and copy the "client_email" value
8. Share the Google Sheet to that email you copied

# Discord Setup
1. Create a new application at https://discord.com/developers/applications
2. Go under the "Bot" tab on the left and click "Add Bot"
3. Copy the bot token

# General Setup
1. Fill out settings.json
- bot_token : The Discord bot token
- bot_prefix : The Discord bot prefix that commands will use
- google_sheet_key : The key to access your Google Sheet (ex. https://docs.google.com/spreadsheets/d/THE_KEY_IS_LOCATED_HERE/)
- log_channel_id : The ID of the Discord channel where the bot will send pending shipment notifications to
- shipping_channel_id : The ID of the Discord channel where the owner can mark items as shipped
- bot_owner_ids : A list of bot owners
2. Run main.py

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

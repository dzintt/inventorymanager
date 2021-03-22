from discord.ext import commands
from discord.utils import get
from discord import Game
import discord, gspread, datetime, os, json, cv2, pdf2image, pyzbar
from pyzbar import pyzbar

#extract variables from setting file
settings = json.load(open("settings.json"))
token, prefix, gsheetKey, logchannel, shipchannel, owners = settings["bot_token"], settings["bot_prefix"], settings["google_sheet_key"], settings["log_channel_id"], settings["shipping_channel_id"], settings["bot_owner_ids"]

#sheet colors
red = {"backgroundColor": {"red": 1.0,"green": 0.5,"blue": 0.5}}
green = {"backgroundColor": {"red": 0.67,"green": 1.0,"blue": 0.54}}
yellow = {"backgroundColor": {"red": 1.0,"green": 0.89,"blue": 0.6}}

#initiate the bot client
client = commands.Bot(command_prefix=prefix)

#bot ready state
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Inventory"))
    print(f'Logged In: {client.user.name}')
    print(f'Invite Link: https://discordapp.com/oauth2/authorize?client_id={client.user.id}&scope=bot&permissions=8')
    print(f'Discord.py Version: {discord.__version__}')
    print('------')
    print('Servers Connected To:')
    async for guild in client.fetch_guilds(limit=150):
        print(guild.name)

    #connect to google sheets
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(gsheetKey)

    #set client variables
    client.worksheet = sh.sheet1
    client.log = client.get_channel(int(logchannel))
    client.shipChannelID = int(shipchannel)
    client.owners = owners

#using on_message instead of a comamnd for ease of use when using a barcode scanner. shipper can scan into the channel and bot will automatically process it
@client.event
async def on_message(message):
    #makes sure that this function does not block other commands from running
    await client.process_commands(message)

    #check if the message is in the shipping channel channel
    if message.channel.id == client.shipChannelID and str(message.author.id) in client.owners:
        database = client.worksheet.get_all_records()

        #check if the trakcing number exists
        outTrackingList = [str(a["Outgoing Tracking"]) for a in database if a["Date Shipped Out"] == ""]
        if message.content in outTrackingList:
            index = outTrackingList.index(message.content)

            #get item data
            user, item, size, tracking, delivered = client.get_user(int(database[index]["Discord ID"])), database[index]["Item"], database[index]["Size"], database[index]["Incoming Tracking"], database[index]["Delivery Date"]
            date = datetime.date.today().strftime("%m/%d/%Y")

            #update sheet
            client.worksheet.format("C" + str(index+2), green)
            client.worksheet.update("I" + str(index+2), date)

            #channel message
            embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"📦 Marked Item As Shipped", timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Item:", value=f"{item} ({size})")
            embed.add_field(name="Incoming Tracking:", value=tracking, inline=False)
            embed.add_field(name="Outgoing Tracking:", value=message.content, inline=False)
            embed.add_field(name="Delivered Date:", value=delivered, inline=False)
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await message.channel.send(embed=embed)

            #notifys the user through DM that their item has been shipped
            embed.title = "🚚 Your Item Has Been Shipped"
            await user.send(embed=embed)
        else:
            #let the user know that their tracking number is invalid
            embed = discord.Embed(colour=discord.Colour(0xf71111), title=f"❌ Tracking Number Does Not Exist Or Is Not Pending Shipment", timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await message.channel.send(embed=embed) 

    
#command to add an item to user inventory
@client.command()
async def add(ctx, tracking, size, *, item):
    #format data and insert into the sheet
    data = [str(ctx.author), str(ctx.author.id), item, size, tracking, datetime.date.today().strftime("%m/%d/%Y")]
    client.worksheet.append_row(data)
    client.worksheet.format("C" + str(len(client.worksheet.get_all_values())), red)

    #channel message
    embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"✅ Successfully Added To Your Inventory", timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="Inventory Manager | Made by DZ#0002")
    embed.add_field(name="Item:", value=f"{item} ({size})")
    embed.add_field(name="Tracking:", value=tracking, inline=False)
    await ctx.send(embed=embed)

#command to remove an item from user inventory
@client.command()
async def remove(ctx, index: int):
    #adjust the index to be more code friendly by subtracting 1
    index -= 1

    #fetch sheet data
    database = client.worksheet.get_all_records()

    #fetch user's active inventory
    userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Shipping Label"] == ""]
    removeItem = userInv[index]

    #find location of item inside the sheet
    index = database.index(removeItem)

    #get item data
    item, size, tracking = database[index]["Item"], database[index]["Size"], database[index]["Incoming Tracking"]

    #delete item
    client.worksheet.delete_rows(index+2)

    #channel message
    embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"✅ Successfully Removed", timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="Inventory Manager | Made by DZ#0002")
    embed.add_field(name="Item:", value=f"{item} ({size})")
    embed.add_field(name="Tracking:", value=tracking, inline=False)
    await ctx.send(embed=embed)

@client.command()
async def inventory(ctx, status):
    #fetch sheet data
    database = client.worksheet.get_all_records()

    #fetch different results based on what the user requests
    if status.lower() == "active":
        userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Shipping Label"] == ""]
    elif status.lower() == "sold":
        userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Shipping Label"] != "" and a["Date Shipped Out"] == ""]
    elif status.lower() == "completed":
        userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Date Shipped Out"] != ""]
    else:
        raise Exception("Invalid Section")

    #display the user's inventory
    if len(userInv) != 0:
        inventory = "\n".join([f"**{userInv.index(i)+1}.** {i['Item']} ({i['Size']}) **|** {i['Delivery Date']}" for i in userInv])
        embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"💰 {ctx.author}'s Inventory ({status.upper()})", description=inventory, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="Inventory Manager | Made by DZ#0002")
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"💰 {ctx.author}'s Inventory ({status.upper()})", description="None", timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="Inventory Manager | Made by DZ#0002")
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

@client.command()
async def sell(ctx, index: int):
    #check if the command contains an .pdf file attachment
    if ctx.message.attachments:
        if ctx.message.attachments[0].filename.endswith(".pdf"):
            #adjust the index to be more code friendly by subtracting 1
            index -= 1

            #get the url of the .pdf file the user sent so it can be inserted into the google sheet later on and be used as a download link
            label = ctx.message.attachments[0].url

            #fetch sheet data
            database = client.worksheet.get_all_records()

            #get the users active inventory
            userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Shipping Label"] == ""]

            #find the index of the item they want to sell
            soldItem = userInv[index]
            index = database.index(soldItem)

            #get item data
            item, size, tracking = database[index]["Item"], database[index]["Size"], database[index]["Incoming Tracking"]

            #save pdf file from discord
            await ctx.message.attachments[0].save(f"./labels/{ctx.message.attachments[0].filename}")

            #convert pdf to jpg for OCR
            pdfImages = pdf2image.convert_from_path(f"./labels/{ctx.message.attachments[0].filename}", poppler_path="./poppler-0.68.0/bin")
            allBarcodes = []

            #scan all images
            for i in range(len(pdfImages)):
                pdfImages[i].save(f"./labels/toscan{i}.jpg", "JPEG")

                #extract the tracking number from the image
                barcodes = pyzbar.decode(cv2.imread(f"./labels/toscan{i}.jpg"))
                for barcode in barcodes:
                    allBarcodes.append(barcode.data.decode("utf-8"))
            
            #find which barcode is the tracking number by length
            outgoingTrack = max(allBarcodes, key=len)
            
            #clear the folder for reuse later and so it does not take up storage
            for f in os.listdir("./labels"):
                os.remove(os.path.join("./labels", f))

            #update sheet with gathered info
            client.worksheet.format("C" + str(index+2), yellow)
            client.worksheet.update("G" + str(index+2), label)
            client.worksheet.update("H" + str(index+2), outgoingTrack)

            #channel message
            embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"⏱️ Item Pending Shipment", description="You will be notified when your item has been shipped out", timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Item:", value=f"{item} ({size})")
            embed.add_field(name="Incoming Tracking:", value=tracking, inline=False)
            embed.add_field(name="Outgoing Tracking:", value=outgoingTrack, inline=False)
            embed.add_field(name="Shipping Label:", value=f"[CLICK HERE]({label})", inline=False)
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await ctx.send(embed=embed)

            #log
            embed.title = f"💵 {ctx.author} Sold An Item"
            embed.description = ""
            embed.set_thumbnail(url=ctx.author.avatar_url)
            await client.log.send(content="@everyone", embed=embed)

        else:
            #user sent a different file format
            embed = discord.Embed(colour=discord.Colour(0xf71111), title=f"❌ Please Send PDF Files Only", timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await ctx.send(embed=embed)
    else:
        #user did not make an attachment to their message
        embed = discord.Embed(colour=discord.Colour(0xf71111), title=f"❌ Missing Shipping Label", timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="Inventory Manager | Made by DZ#0002")
        await ctx.send(embed=embed)

@client.command()
async def unsell(ctx, index: int):
    #adjust the index to be more code friendly by subtracting 1
    index -= 1

    #fetch sheet data
    database = client.worksheet.get_all_records()

    #fetch the user's sold inventory
    userInv = [a for a in database if a["Discord ID"] == ctx.author.id and a["Shipping Label"] != "" and a["Date Shipped Out"] == ""]

    #find the index of the sold item inside the sheet
    soldItem = userInv[index]
    index = database.index(soldItem)

    #get item data
    item, size, tracking = database[index]["Item"], database[index]["Size"], database[index]["Incoming Tracking"]

    #update the item from sold to active state
    client.worksheet.format("C" + str(index+2), red)
    client.worksheet.update("G" + str(index+2), "")
    client.worksheet.update("H" + str(index+2), "")

    #log
    embed = discord.Embed(colour=discord.Colour(0xfcd303), title=f"⏪ {ctx.author} Retracted A Pending Item", timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Item:", value=f"{item} ({size})")
    embed.add_field(name="Incoming Tracking:", value=tracking, inline=False)
    embed.set_footer(text="Inventory Manager | Made by DZ#0002")
    embed.set_thumbnail(url=ctx.author.avatar_url)
    await client.log.send(content="@everyone", embed=embed)

    #channel message
    embed = discord.Embed(colour=discord.Colour(0xfcd303), title=f"⏪ Retracted Item From Pending Shipment", timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Item:", value=f"{item} ({size})")
    embed.add_field(name="Incoming Tracking:", value=tracking, inline=False)
    embed.set_footer(text="Inventory Manager | Made by DZ#0002")
    await ctx.send(embed=embed)



#owner commands

@client.command()
async def toship(ctx):
    #check if the user is a owner
    if str(ctx.author.id) in client.owners:

        #fetch sheet data
        database = client.worksheet.get_all_records()

        #feth a list of items that need to be shippped
        needsShip = [a for a in database if a["Shipping Label"] != "" and a["Date Shipped Out"] == ""]

        #displays the items
        if len(needsShip) != 0:
            inventory = "\n".join([f"**{needsShip.index(i)+1}.** {i['Item']} ({i['Size']}) **|** Label: [CLICK HERE]({i['Shipping Label']})" for i in needsShip])
            embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"⌛ Items That Need To Be Shipped", description=inventory, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=discord.Colour(0x4ef542), title=f"⌛ Items That Need To Be Shipped", description="None", timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="Inventory Manager | Made by DZ#0002")
            await ctx.send(embed=embed)

#error handling
@client.event
async def on_command_error(ctx, error):
    embed = discord.Embed(colour=discord.Colour(0xf71111), title=f"❌ An Unexpected Error Occurred", description=str(error), timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="Inventory Manager | Made by DZ#0002")
    await ctx.send(embed=embed)

#run the bot
client.run(token)
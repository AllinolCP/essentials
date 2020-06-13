from houdini.plugins import IPlugin
from houdini import commands
from houdini.data.penguin import Penguin
from houdini import permissions
from houdini.data.room import Room
from houdini.handlers.play.moderation import moderator_ban,moderator_kick
import difflib
import asyncio
from houdini.data.moderator import Ban


class Essentials(IPlugin):
    author = "Solero"
    description = "Essentials plugin"
    version = "1.0.0"

    def __init__(self, server):
        super().__init__(server)

        self.items_by_name = None

    async def ready(self):
        await self.server.permissions.register('essentials.jr')
        await self.server.permissions.register('essentials.ai')
        await self.server.permissions.register('essentials.ac')
        await self.server.permissions.register('essentials.ban')  
        await self.server.permissions.register('essentials.kick')
        await self.server.permissions.register('essentials.tp')
        await self.server.permissions.register('essentials.summon')
        self.items_by_name = {item.name: item for item in self.server.items.values()}

    @commands.command('room', alias=['jr'])
    @permissions.has_or_moderator('essentials.jr')
    async def join_room(self, p, room: Room):
        if room is not None:
            await p.join_room(room)
        else:
            await p.send_xt('mm', 'Room does not exist', p.id)

    @commands.command('ban')
    @permissions.has_or_moderator('essentials.ban') #Example !BAN Allinol NotCool 24
    async def ban_penguin(self, p, player: str, message: str = 'Banned by a Moderator', duration: int): #added default reason so there is no error
      try:
        player = player.lower()
        penguin_id = await Penguin.select('id').where(Penguin.username == player).gino.first()
        if penguin_id == None:
            await p.send_xt('mm', 'Player is not Valid!', p.id)
            return
        else:
            penguin_id = int(penguin_id[0])
        banned = p.server.penguins_by_id[penguin_id]
        if duration == 0:
            await Penguin.update.values(permaban=True).where(Penguin.username == player).gino.status()
            await banned.close()
            return
        else:
            await moderator_ban(p, penguin_id, hours=duration, comment=message)   
            await banned.close()
            return
      except AttributeError:
        await p.send_xt('mm', 'Player is not Valid', p.id)

    @commands.command('unban')
    @permissions.has_or_moderator('essentials.ban')
    async def unban_penguin(self, p, player: str, duration: int = 24):
    player = player.lower() 
    penguin_id = await Penguin.select('id').where(Penguin.username == player).gino.first()
    if penguin_id == None:
        await p.send_xt('mm', 'Player is not Valid!', p.id)
        return
    else:
        penguin_id = int(penguin_id[0])       
    if duration == 0:
        await Penguin.update.values(permaban=False).where(Penguin.username == player).gino.status()
    else:
        await Ban.delete.where(Ban.penguin_id == penguin_id).gino.status()


    @commands.command('kick')
    @permissions.has_or_moderator('essentials.kick')
    async def kick_penguin(self, p, player: str):
        try:
            player = player.lower()
            penguin_id = await Penguin.select('id').where(Penguin.username == player).gino.first()
            if penguin_id == None:
                await p.send_xt('mm', 'Player is not Valid!', p.id)
                return
            else:
                penguin_id = int(penguin_id[0])
            await moderator_kick(p, penguin_id)
        except AttributeError:
            await p.send_xt('mm', 'Player is not Valid', p.id)


    @commands.command('ai')
    @permissions.has_or_moderator('essentials.ai')
    async def add_item(self, p, *item_query: str):
        item_query = ' '.join(item_query)

        try:
            if item_query.isdigit():
                item = self.server.items[int(item_query)]
            else:
                item_name = difflib.get_close_matches(item_query, self.items_by_name.keys(), n=1)
                item = self.items_by_name[item_name[0]]

            await p.add_inventory(item, cost=0)
        except (IndexError, KeyError):
            await p.send_xt('mm', 'Item does not exist', p.id)

    @commands.command('ac')
    @permissions.has_or_moderator('essentials.ac')
    async def add_coins(self, p, amount: int = 100):
            await p.add_coins(amount, stay=True)  
            
    @commands.command('pay')
    async def pay_coins(self, p, receiver, amount: int):
        receiver = receiver.lower()
        count = await Penguin.select('coins').where(Penguin.id == p.id).gino.first()
        count = int(count[0])
        receivercount = await Penguin.select('coins').where(Penguin.username == receiver).gino.first()
        receivercount = int(receivercount[0])
        prid = await Penguin.select('id').where(Penguin.username == receiver).gino.first()
        prid = int(prid[0])
        try:
            t = p.server.penguins_by_id[prid]
            if amount <= 0:
                await p.send_xt('mm', 'Please enter a valid number', p.id)
            else:
                if p.username == receiver:
                    await p.send_xt('mm', "You can't transfer to yourself!", p.id)
                    return
                else:
                    if count < amount:
                        await p.send_xt('mm', 'You dont have enough coins to transfer', p.id)
                    else:
                        updatedamount = count - amount
                        sentamount = receivercount + amount
                        await p.update(coins=count - amount).apply()
                        await t.update(coins=receivercount + amount).apply()
                        await p.send_xt('cdu', updatedamount, updatedamount)
                        await t.send_xt('cdu', sentamount, sentamount)
                        await p.send_xt('mm', f'successfully transfered {amount} to {receiver}', p.id)
                        await t.send_xt('mm', f"You've received {amount} from {p.username}", prid)
        except KeyError:
            await p.send_xt('mm', 'Player is not Online', p.id)
            
    @commands.command('tp')
    @permissions.has_or_moderator('essentials.tp')
    async def tp(self, p, player):
        player = player.lower()
        prid = await Penguin.select('id').where(Penguin.username == player).gino.first()
        prid = int(prid[0])
        try:
            t = p.server.penguins_by_id[prid]
            await p.join_room(t.room)
        except KeyError:
            await p.send_xt('mm', 'Player is not Online', p.id)

    @commands.command('summon')
    @permissions.has_or_moderator('essentials.summon')
    async def summon(self, p, player):
        player = player.lower()
        prid = await Penguin.select('id').where(Penguin.username == player).gino.first()
        prid = int(prid[0])
        try:
            t = p.server.penguins_by_id[prid]
            await t.join_room(p.room)
        except KeyError:
            await p.send_xt('mm', 'Player is not Online', p.id)

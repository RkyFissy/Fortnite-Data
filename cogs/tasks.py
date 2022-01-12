from discord_webhook import DiscordWebhook, DiscordEmbed
from discord.ext import commands, tasks
import traceback
import aiohttp
import logging
import asyncio
import json
import time

import discord_webhook

import util

log = logging.getLogger('FortniteData.cogs.tasks')

class Tasks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ClientSession = aiohttp.ClientSession

        log.debug('Starting tasks...')
        try:
            self.updates_check.start()
        except:
            log.critical(f'An error ocurred starting one or more tasks. Traceback:\n{traceback.format_exc()}')

    ###
    ## Updates Channel Stuff
    ###

    @tasks.loop(minutes=4)
    async def updates_check(self):

        while True:
            if util.ready == True: # start checking only if the bot is completely ready
                break
            else:
                await asyncio.sleep(1)

        log.debug('Executing "tasks.updates_check" task')

        try: # New cosmetics

            log.debug(f'Checking cosmetic updates...')

            for lang in util.configuration['languages']:

                cached_cosmetics = json.load(open(f'cache/cosmetics/all_{lang}.json', 'r', encoding='utf-8'))
                new_cosmetics = await util.fortniteapi[lang]._load_cosmetics()

                cached_cosmetic_ids = [i['id'] for i in cached_cosmetics['data']] # List of every cosmetic ID

                start_timestamp = time.time()
                new_cosmetics_list = []

                for cosmetic in new_cosmetics:

                    if cosmetic['id'] not in cached_cosmetic_ids:

                        new_cosmetics_list.append(cosmetic)


                if len(new_cosmetics_list) > 0:

                    log.debug(f'Building embeds for {len(new_cosmetics_list)} new cosmetics...')

                    embeds = []

                    count = 0
                    for i in new_cosmetics_list:

                        color = str(util.get_color_by_rarity(i['rarity']['value']))

                        embed = DiscordEmbed()
                        if count == 0:
                            embed.set_author(name=util.get_str(lang, 'update_message_string_new_cosmetics_detected'))

                        embed.title = f'{i["name"]}'

                        embed.description = f'{i["description"]}'

                        embed.color = color.replace('0x', '')

                        embed.add_embed_field(name=util.get_str(lang, 'command_string_id'), value=f'`{i["id"]}`', inline=False)

                        embed.add_embed_field(name=util.get_str(lang, 'command_string_type'), value=f'`{i["type"]["displayValue"]}`', inline=False)

                        embed.add_embed_field(name=util.get_str(lang, 'command_string_rarity'), value=f'`{i["rarity"]["displayValue"]}`', inline=False)

                        if i['introduction'] != None:
                            embed.add_embed_field(name=util.get_str(lang, 'command_string_introduction'), value=f'`{i["introduction"]["text"]}`', inline=False)
                        else:
                            embed.add_embed_field(name=util.get_str(lang, 'command_string_introduction'), value=util.get_str(lang, 'command_string_not_introduced_yet'), inline=False)

                        if i['set'] != None:
                            embed.add_embed_field(name=util.get_str(lang, 'command_string_set'), value=f'`{i["set"]["text"]}`', inline=False)
                        else:
                            embed.add_embed_field(name=util.get_str(lang, 'command_string_set'), value=util.get_str(lang, 'command_string_none'), inline=False)

                        embed.set_thumbnail(url=i['images']['icon'])
                        count += 1

                        if count == len(new_cosmetics):
                            embed.set_footer(text=util.get_str(lang, 'command_string_int_of_int_with_credits').format(count = count, total = len(new_cosmetics_list)))
                        else:
                            embed.set_footer(text=util.get_str(lang, 'command_string_int_of_int').format(count = count, total = len(new_cosmetics_list)))


                        embeds.append(embed)

                    result = await self.updates_channel_send(embeds=embeds, type_='cosmetics', lang=lang)

                    log.debug(f'Sent {len(embeds)} embeds to {len(result)} guilds in {int((time.time() - start_timestamp))} seconds! - Status: {result}')
                
                else:

                    log.debug('No cosmetic changes detected.')
                    break

        except Exception:
            log.error(f'Failed while checking upcoming cosmetics changes. Traceback:\n{traceback.format_exc()}')

        try: # ingame news

            log.debug(f'Checking ingame news updates...')

            for lang in util.configuration['languages']:

                cached_news = json.load(open(f'cache/news/{lang}.json', 'r', encoding='utf-8'))
                new_news = await util.fortniteapi[lang].get_news(language = lang)

                to_send_list = []

                if new_news['data']['br'] != None:

                    br_motds = []

                    if cached_news['data']['br']['hash'] != new_news['data']['br']['hash']:

                        for motd in new_news['data']['br']['motds']:
                            if motd not in cached_news['data']['br']['motds']:
                                br_motds.append(motd)

                        sorted_br_motds = sorted(br_motds, key = lambda x: x['sortingPriority'], reverse = True)
                        count = 0
                        for motd in sorted_br_motds:

                            embed = DiscordEmbed()
                            if count == 0:
                                embed.set_author(name=util.get_str(lang, 'update_message_string_br_news_updated'))

                            embed.title = motd['title']

                            embed.description = motd['body']

                            embed.color = 0x3498db

                            embed.set_image(url = motd['image'])

                            count += 1

                            if count == len(br_motds):
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int_with_credits').format(count = count, total = len(sorted_br_motds)))
                            else:
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int').format(count = count, total = len(sorted_br_motds)))
                            
                            to_send_list.append(embed)
                    
                    else:
                        log.debug(f'[{lang}] No br news changes found')

                if new_news['data']['creative'] != None:

                    cr_motds = []

                    if cached_news['data']['creative']['hash'] != new_news['data']['creative']['hash']:

                        for motd in new_news['data']['creative']['motds']:
                            if motd not in cached_news['data']['creative']['motds']:
                                cr_motds.append(motd)

                        sorted_cr_motds = sorted(cr_motds, key = lambda x: x['sortingPriority'], reverse = True)
                        count = 0
                        for motd in sorted_cr_motds:

                            embed = DiscordEmbed()
                            if count == 0:
                                embed.set_author(name=util.get_str(lang, 'update_message_string_creative_news_updated'))

                            embed.title = motd['title']

                            embed.description = motd['body']

                            embed.color = 0x3498db

                            embed.set_image(url = motd['image'])

                            count += 1

                            if count == len(sorted_cr_motds):
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int_with_credits').format(count = count, total = len(sorted_cr_motds)))
                            else:
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int').format(count = count, total = len(sorted_cr_motds)))
                            
                            to_send_list.append(embed)
                    
                    else:
                        log.debug(f'[{lang}] No creative news changes found')

                if new_news['data']['stw'] != None:

                    stw_motds = []

                    if cached_news['data']['stw']['hash'] != new_news['data']['stw']['hash']:

                        for motd in new_news['data']['stw']['messages']:
                            if motd not in cached_news['data']['stw']['messages']:
                                stw_motds.append(motd)

                        count = 0
                        for motd in stw_motds:

                            embed = DiscordEmbed()
                            if count == 0:
                                embed.set_author(name=util.get_str(lang, 'update_message_string_stw_news_updated'))

                            embed.title = motd['title']

                            embed.description = motd['body']

                            embed.color = 0x3498db

                            embed.set_image(url = motd['image'])

                            count += 1

                            if count == len(br_motds):
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int_with_credits').format(count = count, total = len(br_motds)))
                            else:
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int').format(count = count, total = len(br_motds)))
                            
                            to_send_list.append(embed)
                    
                    else:
                        log.debug(f'[{lang}] No stw news changes found')

                if len(to_send_list) != 0:

                    with open(f'cache/news/{lang}.json', 'w', encoding='utf-8') as f:
                        json.dump(new_news, f)

                    result = await self.updates_channel_send(embeds=to_send_list, type_='news', lang=lang)

                    log.debug(f'Sent {len(to_send_list)} embeds to {len(result)} guilds in {int((time.time() - start_timestamp))} seconds! - Status: {result}')

                else:

                    break

        except:
            log.error(f'Failed while checking ingame news changes. Traceback:\n{traceback.format_exc()}')

        try: # playlists

            log.debug(f'Checking cosmetic updates...')

            for lang in util.configuration['languages']:

                cached_playlists = json.load(open(f'cache/playlists/{lang}.json', 'r', encoding='utf-8'))
                new_playlists = await util.fortniteapi[lang].get_playlists(language = lang)

                added_playlists = []

                if len(cached_playlists['data']) != len(new_playlists['data']):

                    to_send_list = []

                    for playlist in new_playlists['data']:
                        if playlist not in cached_playlists['data']:

                            added_playlists.append(playlist)

                    if len(added_playlists) != 0:

                        count = 0

                        for playlist in added_playlists:

                            embed = DiscordEmbed()
                            if count == 0:
                                embed.set_author(name=util.get_str(lang, 'update_message_string_new_playlists_detected'))

                            embed.title = playlist['name']

                            if playlist['description'] != None:
                                embed.description = playlist['description']
                            
                            else:
                                embed.description = util.get_str(lang, 'update_message_string_playlist_no_description')

                            embed.color = 0x3498db

                            if playlist['images']['showcase'] != None:
                                embed.set_image(url = playlist['images']['showcase'])

                            footer_icon = None
                            if playlist['images']['missionIcon'] != None:
                                footer_icon = playlist['images']['missionIcon']

                            count += 1

                            if count == len(br_motds):
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int_with_credits').format(count = count, total = len(added_playlists)), icon_url = footer_icon)
                            else:
                                embed.set_footer(text = util.get_str(lang, 'command_string_int_of_int').format(count = count, total = len(added_playlists)), icon_url = footer_icon)
                            
                            to_send_list.append(embed)


                    with open(f'cache/playlists/{lang}.json', 'w', encoding='utf-8') as f:
                        json.dump(new_playlists, f)

                    result = await self.updates_channel_send(embeds=to_send_list, type_='playlists', lang=lang)

                    log.debug(f'Sent {len(to_send_list)} embeds to {len(result)} guilds in {int((time.time() - start_timestamp))} seconds! - Status: {result}')


        except:
            log.error(f'Failed while checking playlists changes. Traceback:\n{traceback.format_exc()}')


    async def updates_channel_send(self, embeds, type_, lang):
        
        servers = list(util.database.guilds.find({'updates_channel.enabled': True, 'language': lang}))

        queues = await self._create_queue(embeds)
        urls = []

        for i in servers:

            if i['updates_channel']['config'][type_] == False:
                continue

            guild = self.bot.get_guild(i['server_id'])

            if guild != None:

                urls.append(i['updates_channel']['webhook'])


        status_codes = []

        webhook = DiscordWebhook(
            url=urls,
            rate_limit_retry=True
        )

        for i in queues:
            
            for em in i:
                webhook.add_embed(em)

            result = webhook.execute(remove_embeds=True)

            status_codes.append(result)

        return status_codes


    async def _create_queue(self, embeds: list): # Separate embeds in lists of 10

        log.debug('Creating embeds queue...')

        master_list = []
        temp_list = []

        master_append_count = 0

        for embed in embeds:

            if len(temp_list) > 9:

                master_append_count += 1

                master_list.append([i for i in temp_list])
                temp_list.clear()

                temp_list.append(embed)
            
            else:

                temp_list.append(embed)

        if master_append_count == 0:
            master_list.append(temp_list)

        log.debug(f'Created {len(master_list)} embed queues!')

        return master_list


def setup(bot):
    bot.add_cog(Tasks(bot))
![Logo](/resources/icon.png)
# QueueBot
QueueBot is a queue generation and managing tool for your discord game nights! It is perfect for games like Halo where matches are quick, game times vary from match to match, and making sure everybody gets a chance to pick a game mode is important. Queues are built right from your current voice channel with flexible management to add, remove, reshuffle and more!
 
 
 ## Add to your server!
 [Add link](https://discord.com/api/oauth2/authorize?client_id=751980977567432764&permissions=36972608&scope=bot)
 
 ## Usage Instructions
 The current hot key is '{' and the commands are as follows:
 
 ### {create
 - Creates player queue from current voice channel. Must be in voice channel to create queue (may add text only version later)
 
 ### {end
 - Deletes queue and bot leaves voice channel
 
 ### Queue Management
 - Other queue management tasks (force adding users, reshuffling, etc) can be done via the built in reaction system
 ![screenshot](/resources/screenshot.png)
 
 ## Self Hosting Instructions
 1. Clone repository/download zip file
 2. Create .env file in root folder of project
 3. Follow these instructions for a token (https://discordpy.readthedocs.io/en/latest/discord.html)
 4. Add 'DISCORD_TOKEN=TOKENHERE' to .env file, replacing 'TOKENHERE' with your token
 5. Add 'PREFIX=YOURPREFIXHERE' to the .env file, replacing 'YOURPREFIXHERE' with your prefix
 6. Save .env file
 7. Run python script OR build docker container using included dockerfile
 8. Follow these instructions to add your bot to your server (https://discordpy.readthedocs.io/en/latest/discord.html)

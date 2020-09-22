# QueueBot
QueueBot is a queue generation and managing tool for your discord game nights! It is perfect for games like Halo where matches are quick, and game times vary from match to match and making sure everybody gets a chance to pick a game mode is important. Queues are built right from your current voice channel with flexible management to add, remove, reshuffle and more!
 
 
 ## Add to your server!
 *Coming Soon!*
 
 ## Usage Instructions
 The current hot key is '?' (changing soon due to so many conflicts) and the commands are as follows:
 
 ### ?create
 - Creates player queue from current voice channel. Must be in voice channel to create queue (may add text only version later)
 
 ### ?add @user
 - Adds specific player if they were missed earlier
 
 ### ?remove @user
 - Removes specific player of they are no longer wanted in the queue
 
 ### ?next
 - Moves current top of list to end of the list and promotes the number two to top of queue
 
 ### ?reshuffle
 - Reshuffles current queue of players
 
 ### ?update
 - Automatically adds or removes players if they have joined/left voice channel
 
 ### ?queue
 - Lists current queue of players
 
 ### ?end
 - Deletes queue and bot leaves voice channel
 
 ## Self Hosting Instructions
 1. Clone repository/download zip file
 2. Create .env file in root folder of project
 3. Follow these intructions to et bot token (https://discordpy.readthedocs.io/en/latest/discord.html)
 4. Add 'DISCORD_TOKEN=TOKENHERE' to .env file, replacing 'TOKENHERE' with your token
 5. Save .env file
 6. Run python script OR build docker container using included dockerfile
 7. Follow these instructions to add your bot to your server (https://discordpy.readthedocs.io/en/latest/discord.html)
 
 


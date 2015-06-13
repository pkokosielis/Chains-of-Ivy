CSV Formats:

These are semi-colon delimited CSV files.

1) monsterList.csv

Add your monsters here in the following format
<monster name> ; <Hit Points> ; <Armor Class> ; <attack desc> ; <experience points given> ; <items given> ; <gold given>

   eg)
   Rebel Automaton;25;20;swings switchblade;30;None;30

2) roomList.csv

Add your room descriptions here in the following format
<unique room id>; <room name> ; <room desc> ; <% chance of encounter>

   eg)
   1; A Dark Cave; You are in a dark cave. There is a light to the west ;35

3) roomAdjList.csv

This file defines which rooms are adjcant to which rooms
In the following format:

<this room id> ; <north room id> ; <south room id>; <east room id> ; <west room id> ; <up room id> ; <down room id>

   eg)
   1;None;None;None;None;None;2

   In this case, Room with ID=1 has one adjcent room in the direction "down"



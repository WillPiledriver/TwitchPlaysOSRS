package net.runelite.client.plugins.TwitchPlaysPlugin;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.http.HttpObjectAggregator;
import io.netty.handler.codec.http.HttpServerCodec;
import io.netty.handler.codec.http.websocketx.CloseWebSocketFrame;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;
import io.netty.handler.codec.http.websocketx.WebSocketServerProtocolHandler;
import io.netty.handler.stream.ChunkedWriteHandler;

import net.runelite.api.*;
import net.runelite.api.coords.WorldPoint;
import net.runelite.api.geometry.SimplePolygon;
import net.runelite.api.coords.LocalPoint;
import net.runelite.api.NPC;
import net.runelite.api.Client;
import net.runelite.api.NPCComposition;
import net.runelite.api.Perspective;
import net.runelite.api.widgets.Widget;
import net.runelite.api.Tile;
import net.runelite.api.ObjectComposition;
import net.runelite.api.GroundObject;
import net.runelite.api.Scene;
import net.runelite.api.Point;
import net.runelite.api.widgets.WidgetInfo;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.eventbus.EventBus;
import net.runelite.api.events.GameStateChanged;

import java.awt.*;
import java.awt.Shape;
import java.awt.geom.PathIterator;
import javax.inject.Inject;
import java.util.ArrayList;
import java.util.List;

@PluginDescriptor(
        name = "Twitch Plays Plugin",
        description = "Your plugin description here",
        tags = {"twitch", "plays"}
)
public class TwitchPlaysPlugin extends Plugin {
    @Inject
    private Client client;
    private Channel channel;

    private GameState lastGameState;


    @Override
    protected void startUp() throws Exception {
        // Create the EventLoopGroup for handling connections
        EventLoopGroup bossGroup = new NioEventLoopGroup();
        EventLoopGroup workerGroup = new NioEventLoopGroup();

        // Configure the server bootstrap
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        // HTTP request/response codec
                        pipeline.addLast(new HttpServerCodec());
                        // ChunkedWriteHandler is required for writing large data such as files
                        pipeline.addLast(new ChunkedWriteHandler());
                        // Aggregates HTTP request into FullHttpRequest/FullHttpResponse
                        pipeline.addLast(new HttpObjectAggregator(65536));
                        // Handles WebSocket handshakes and frames
                        pipeline.addLast(new WebSocketServerProtocolHandler("/"));
                        // Your WebSocket handler
                        pipeline.addLast(new YourWebSocketHandler());
                    }
                });

        // Start the server
        channel = bootstrap.bind(8085).sync().channel();
    }

    @Override
    protected void shutDown() throws Exception {
        // Close the channel and release resources
        if (channel != null) {
            channel.close().sync();
        }
    }

    @Subscribe
    private void onGameStateChanged(GameStateChanged ev)
    {
        System.out.println(ev.getGameState());

        /*if (ev.getGameState() == GameState.LOGIN_SCREEN) {
            ctxMain.writeAndFlush(buildJSON("login", "ready"));
        } else if (ev.getGameState() == GameState.LOGGING_IN){
            ctxMain.writeAndFlush(buildJSON("login", "logging in"));
        } else if (ev.getGameState() == GameState.LOGGED_IN) {
            ctxMain.writeAndFlush(buildJSON("login", "logged in"));
        }*/
    }

    public static SimplePolygon extractSimplePolygon(Shape shape) {
        List<Integer> xCoordinates = new ArrayList<>();
        List<Integer> yCoordinates = new ArrayList<>();

        PathIterator pathIterator = shape.getPathIterator(null);
        float[] coords = new float[6];

        while (!pathIterator.isDone()) {
            int type = pathIterator.currentSegment(coords);
            switch (type) {
                case PathIterator.SEG_MOVETO:
                case PathIterator.SEG_LINETO:
                    xCoordinates.add((int) coords[0]);
                    yCoordinates.add((int) coords[1]);
                    break;
                // If you need to handle other segment types, you can add cases here.
            }
            pathIterator.next();
        }

        // Convert lists to arrays
        int[] xCoordsArray = xCoordinates.stream().mapToInt(Integer::intValue).toArray();
        int[] yCoordsArray = yCoordinates.stream().mapToInt(Integer::intValue).toArray();

        // Create and return the SimplePolygon object with the extracted coordinates
        return new SimplePolygon(xCoordsArray, yCoordsArray, xCoordsArray.length - 1);
    }


    public Shape getGameItemClickboxByPartialName(String partialName) {
        Scene scene = client.getScene();

        int playerPlane = client.getPlane();
        int distance = Integer.MAX_VALUE;
        WorldPoint playerPos = client.getLocalPlayer().getWorldLocation();
        Tile[][][] tiles = scene.getTiles();
        SimplePolygon sp = new SimplePolygon();

        for (int x = 0; x < Perspective.SCENE_SIZE; x++) {
            for (int y = 0; y < Perspective.SCENE_SIZE; y++) {
                // Get the tile at the specified coordinates
                Tile tile = tiles[playerPlane][x][y];
                if (tile != null) {
                    List<TileItem> til = tile.getGroundItems();
                    if (til != null){
                        for (TileItem ti : til) {
                            if (client.getItemDefinition(ti.getId()).getName().toLowerCase().contains(partialName.toLowerCase())) {
                                if (tile.getWorldLocation().distanceTo2D(playerPos) < distance) {
                                    distance = tile.getWorldLocation().distanceTo2D(playerPos);
                                    Shape cb = Perspective.getClickbox(client, ti.getModel(), 0, tile.getLocalLocation().getX(), tile.getLocalLocation().getY(), Perspective.getTileHeight(client, tile.getLocalLocation(), client.getPlane()));
                                    if (cb != null) {
                                        sp = extractSimplePolygon(cb);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (distance == Integer.MAX_VALUE) {
            return null;
        }
        return sp;
    }

    public Shape getTileObjectClickboxByPartialName(String partialName) {
        Scene scene = client.getScene();

        int playerPlane = client.getPlane();
        int distance = Integer.MAX_VALUE;
        WorldPoint playerPos = client.getLocalPlayer().getWorldLocation();
        Tile[][][] tiles = scene.getTiles();
        SimplePolygon sp = new SimplePolygon();

        // Loop through each tile in the playerPlane, x, and y coordinates
        for (int x = 0; x < Perspective.SCENE_SIZE; x++) {
            for (int y = 0; y < Perspective.SCENE_SIZE; y++) {
                // Get the tile at the specified coordinates
                Tile tile = tiles[playerPlane][x][y];
                if (tile != null) {
                    // Perform actions on the tile or its contents
                    // Example: Get the IDs of objects on the tile and print them
                    for (TileObject tileObject : tile.getGameObjects()) {
                        if (tileObject != null) {
                            if (!client.getObjectDefinition(tileObject.getId()).getName().equals("null")){
                                //System.out.println(client.getObjectDefinition(tileObject.getId()).getName());
                            }
                            int objectID = tileObject.getId();
                            ObjectComposition oc = client.getObjectDefinition(objectID);
                            // Do something with the object ID
                            if (!oc.getName().equals("null")) {
                                if (oc.getName().toLowerCase().contains(partialName.toLowerCase())) {
                                    if (tileObject.getWorldLocation().distanceTo2D(playerPos) < distance) {
                                        distance = tileObject.getWorldLocation().distanceTo2D(playerPos);
                                        Shape cb = tileObject.getClickbox();
                                        if (cb != null) {
                                            sp = extractSimplePolygon(cb);
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Wall Objects

                    WallObject wo = tile.getWallObject();
                    if (wo != null) {
                        if (!client.getObjectDefinition(wo.getId()).getName().equals("null")){
                            //System.out.println(client.getObjectDefinition(wo.getId()).getName());
                        }
                        if (client.getObjectDefinition(wo.getId()).getName().toLowerCase().contains(partialName.toLowerCase())) {
                            if (wo.getWorldLocation().distanceTo2D(playerPos) < distance) {
                                distance = wo.getWorldLocation().distanceTo2D(playerPos);
                                Shape cb = wo.getClickbox();
                                if (cb != null) {
                                    sp = extractSimplePolygon(cb);
                                }
                            }
                        }
                    }

                    // ground object
                    GroundObject go = tile.getGroundObject();
                    if (go != null) {
                        if (!client.getObjectDefinition(go.getId()).getName().equals("null")){
                            //System.out.println(client.getObjectDefinition(go.getId()).getName());
                        }
                        if (client.getObjectDefinition(go.getId()).getName().toLowerCase().contains(partialName.toLowerCase())) {
                            if (go.getWorldLocation().distanceTo2D(playerPos) < distance) {
                                distance = go.getWorldLocation().distanceTo2D(playerPos);
                                Shape cb = go.getClickbox();
                                if (cb != null) {
                                    sp = extractSimplePolygon(cb);
                                }
                            }
                        }
                    }

                    // decorative object
                    DecorativeObject deco = tile.getDecorativeObject();
                    if (deco != null) {
                        if (!client.getObjectDefinition(deco.getId()).getName().equals("null")){
                            //System.out.println(client.getObjectDefinition(deco.getId()).getName());
                        }
                        if (client.getObjectDefinition(deco.getId()).getName().toLowerCase().contains(partialName.toLowerCase())) {
                            if (deco.getWorldLocation().distanceTo2D(playerPos) < distance) {
                                distance = deco.getWorldLocation().distanceTo2D(playerPos);
                                Shape cb = deco.getClickbox();
                                if (cb != null) {
                                    sp = extractSimplePolygon(cb);
                                }
                            }
                        }
                    }
                }
            }
        }
        if (distance == Integer.MAX_VALUE) {
            return null;
        }
        return sp;
    }

    public void getTileObjectsID() {
        LocalPoint player = client.getLocalPlayer().getLocalLocation();
        Scene scene = client.getScene();

        int playerPlane = client.getPlane();

        Tile[][][] tiles = scene.getTiles();

        // Loop through each tile in the playerPlane, x, and y coordinates
        for (int x = 0; x < Perspective.SCENE_SIZE; x++) {
            for (int y = 0; y < Perspective.SCENE_SIZE; y++) {
                // Get the tile at the specified coordinates
                Tile tile = tiles[playerPlane][x][y];

                if (tile != null) {
                    // Perform actions on the tile or its contents
                    // Example: Get the IDs of objects on the tile and print them
                    for (TileObject tileObject : tile.getGameObjects()) {
                        if (tileObject != null) {
                            int objectID = tileObject.getId();
                            ObjectComposition oc = client.getObjectDefinition(objectID);
                            // Do something with the object ID
                            if (!oc.getName().equals("null")) {
                                //Shape cb = tileObject.getClickbox();
                                // System.out.println("Object Name: " + oc.getName() + ", (" + x + ", " + y + ")");
                            }
                        }
                    }

                    if (tile.getGroundItems() != null) {
                        List<TileItem> groundItems = tile.getGroundItems();
                        for (TileItem ti: groundItems) {
                            int id = ti.getId();
                            ItemComposition ic = client.getItemDefinition(id);
                            //Shape cb = Perspective.getClickbox(client, ti.getModel(), 0, tile.getLocalLocation().getX(), tile.getLocalLocation().getY(), Perspective.getTileHeight(client, tile.getLocalLocation(), playerPlane));
                            System.out.println(ic.getName());
                        }
                    }
                }
            }
        }
    }

    public void findAllLoot() {
        Scene scene = client.getScene();
        int playerPlane = client.getPlane();
        Tile[][][] tiles = scene.getTiles();

        // Loop through each tile in the playerPlane, x, and y coordinates
        for (int x = 0; x < Perspective.SCENE_SIZE; x++) {
            for (int y = 0; y < Perspective.SCENE_SIZE; y++) {
                // Get the tile at the specified coordinates
                Tile tile = tiles[playerPlane][x][y];
                if (tile != null) {
                    /*GameObject[] gameObjects = tile.getGameObjects();
                    if (gameObjects != null) {
                        for (GameObject go : gameObjects) {
                            if (go != null) {
                                System.out.println(client.getObjectDefinition(go.getId()).getName());
                            }
                        }
                    }*/
                    List<TileItem> til = tile.getGroundItems();
                    if (til != null){
                        for (TileItem ti : til) {
                            System.out.println(client.getItemDefinition(ti.getId()).getName());
                        }
                    }
                }
            }
        }
    }

    // ... (findItemPositionsByPartialName and other methods remain the same)
    public List<Point> findItemPositionsByPartialName(String partialName) {
        List<Point> positions = new ArrayList<>();

        Widget inventoryWidget = client.getWidget(WidgetInfo.INVENTORY);

        int inventoryScreenX = -1;
        int inventoryScreenY = -1;
        int inventoryWidth = -1;
        int inventoryHeight = -1;

        // Check if the Inventory component is valid
        if (inventoryWidget != null) {
            // Retrieve the bounds (bounding box) of the Inventory component
            Rectangle inventoryBounds = inventoryWidget.getBounds();

            // Get the screen coordinates (X and Y) of the top-left corner of the inventory
            inventoryScreenX = (int) inventoryBounds.getX();
            inventoryScreenY = (int) inventoryBounds.getY();
            inventoryWidth = inventoryBounds.width;
            inventoryHeight = inventoryBounds.height;

            // Now you have the screen coordinates of the inventory to use in your plugin
            System.out.println("Inventory Screen Coordinates: X=" + inventoryScreenX + ", Y=" + inventoryScreenY);
        }

        // Check if the inventory is valid
        ItemContainer inventory = client.getItemContainer(InventoryID.INVENTORY);

        // Check if the inventory is valid
        if (inventory != null) {
            // Get all the items in the inventory
            Item[] items = inventory.getItems();

            // Loop through the items and find the positions of items with the given partial name
            for (int i = 0; i < items.length; i++) {
                Item item = items[i];
                // Get the item ID and check if it's valid
                int itemId = item.getId();

                if (itemId != -1) {
                    // Get the item composition using the item ID
                    ItemComposition itemComposition = client.getItemDefinition(itemId);

                    // Check if the item composition is valid and its name contains the partial name
                    if (itemComposition.getName().toLowerCase().contains(partialName.toLowerCase())) {
                        // Calculate the X and Y coordinates based on the 1D index
                        int x = i % 4;
                        int y = i / 4;

                        // Calculate the screen coordinates of the item
                        int itemScreenX = inventoryScreenX + (x * inventoryWidth / 4) + ((inventoryWidth / 4) / 2);
                        int itemScreenY = inventoryScreenY + (y * inventoryHeight / 7) + ((inventoryHeight / 7) / 2);

                        // Add the X and Y coordinates to the list
                        positions.add(new Point(itemScreenX, itemScreenY));
                    }
                }
            }
        }

        return positions;
    }

    /**
     * Finds the closest NPC in the game world whose name contains the given partial name.
     *
     * @param partialName The partial name of the NPC to search for.
     * @return The closest NPC found with a name containing the given partial name, or null if not found.
     */
    private NPC findClosestNPCByPartialName(String partialName) {
        try {
            // Get the player's local location
            LocalPoint playerLocalLocation = client.getLocalPlayer().getLocalLocation();
            List<String> npcNames = new ArrayList<>();

            // Initialize variables to track the closest NPC and its distance to the player
            NPC closestNPC = null;
            int closestDistance = Integer.MAX_VALUE;

            // Get all the NPCs in the game
            List<NPC> npcs = client.getNpcs();

            // Check if NPCs exist
            if (npcs == null) {
                return null;
            }
            // Loop through the NPCs and find the NPC with the given partial name closest to the player
            for (NPC npc : npcs) {
                NPCComposition npcComposition = npc.getComposition();

                if (npcComposition != null) {
                    if (!npcComposition.getName().equals("null")) {
                        String npcName = npcComposition.getName().toLowerCase();
                        npcNames.add(npcName);
                        if (npcName.contains(partialName.toLowerCase())) {
                            // Calculate the distance between the player and the NPC
                            LocalPoint npcLocalLocation = npc.getLocalLocation();
                            int distance = playerLocalLocation.distanceTo(npcLocalLocation);

                            // Update the closest NPC and distance if needed
                            if (distance < closestDistance) {
                                closestNPC = npc;
                                closestDistance = distance;
                            }
                        }
                    }
                }
            }

            System.out.println(String.join(", ", npcNames));
            return closestNPC;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    private Shape getHullClosestNPC(String partialName) {
        NPC npc = findClosestNPCByPartialName(partialName);
        if (npc == null) {
            return null;
        } else {
            Shape cb = Perspective.getClickbox(client, npc.getModel(), npc.getCurrentOrientation(), npc.getLocalLocation().getX(), npc.getLocalLocation().getY(), Perspective.getTileHeight(client, npc.getLocalLocation(), client.getPlane()));
            Shape ch = npc.getConvexHull();
            return extractSimplePolygon(cb);
        }
    }

    private NPC findNPCByPartialName(String partialName) {
        // Get all the NPCs in the game
        NPC[] npcs = client.getNpcs().toArray(new NPC[0]);

        // Check if NPCs exist
        if (npcs == null) {
            return null;
        }

        // Loop through the NPCs and find the NPC with the given partial name
        for (NPC npc : npcs) {
            NPCComposition npcComposition = npc.getComposition();

            if (npcComposition != null) {
                // Check if the NPC name contains the partial name
                String npcName = npcComposition.getName().toLowerCase();

                if (npcName.contains(partialName.toLowerCase())) {
                    return npc;
                }
            }
        }

        return null;
    }

    public TextWebSocketFrame buildJSON(String action, Object query) {
        JsonObject responseJson = new JsonObject();
        responseJson.addProperty("action", action);
        responseJson.add("response", new Gson().toJsonTree(query));
        String response = responseJson.toString();
        // System.out.println(response);
        return new TextWebSocketFrame(response);
    }

    public class YourWebSocketHandler extends ChannelInboundHandlerAdapter {
        @Override
        public void channelActive(ChannelHandlerContext ctx) {
            System.out.println("Connection established");
            // Handle WebSocket connection
        }

        @Override
        public void channelInactive(ChannelHandlerContext ctx) {
            System.out.println("Connection terminated");
            // Handle WebSocket disconnection
        }

        @Override
        public void channelRead(ChannelHandlerContext ctx, Object msg) {
            // Handle incoming WebSocket frames
            if (msg instanceof TextWebSocketFrame) {
                TextWebSocketFrame frame = (TextWebSocketFrame) msg;
                JsonObject jsonObject = new JsonParser().parse(frame.text()).getAsJsonObject();
                String action = jsonObject.get("action").getAsString();
                String query = jsonObject.get("query").getAsString();
                switch (action) {
                    case "drop":
                        List<Point> dropPositions = findItemPositionsByPartialName(query);
                        ctx.writeAndFlush(buildJSON(action, dropPositions));
                        break;

                    case "heartbeat":
                        /*JsonObject jo = new JsonObject();
                        jo.addProperty("xOffset", client.getViewportXOffset());
                        jo.addProperty("yOffset", client.getViewportYOffset());
                        jo.addProperty("viewportWidth", client.getViewportWidth());
                        jo.addProperty("viewportHeight", client.getViewportHeight());
                        ctx.writeAndFlush(buildJSON(action, jo));*/
                        if (client.getGameState() == GameState.LOGIN_SCREEN) {
                            lastGameState = client.getGameState();
                            ctx.writeAndFlush(buildJSON("login", "ready"));
                        } else if (client.getGameState() == GameState.LOGGED_IN && lastGameState != GameState.LOGGED_IN) {
                            lastGameState = client.getGameState();
                            ctx.writeAndFlush(buildJSON("login", "logged in"));
                        }
                        break;

                    case "npc":
                        Shape n = getHullClosestNPC(query);
                        ctx.writeAndFlush(buildJSON(action, n));
                        break;

                    case "tile":
                        Shape cb = getTileObjectClickboxByPartialName(query);
                        ctx.writeAndFlush(buildJSON(action, cb));
                        break;

                    case "loot":
                        Shape loot = getGameItemClickboxByPartialName(query);
                        ctx.writeAndFlush(buildJSON(action, loot));
                        break;

                    case "login":
                        System.out.println(jsonObject.get("username").getAsString());
                        client.setUsername(jsonObject.get("username").getAsString());
                        client.setPassword(jsonObject.get("password").getAsString());
                        break;

                    case "message":
                        String user = jsonObject.get("user").getAsString();
                        String message = jsonObject.get("msg").getAsString();
                        client.addChatMessage(ChatMessageType.CLAN_CHAT, user, message, "TWITCH");

                    default:
                        // Handle unknown actions or errors here
                        break;
                }
            } else if (msg instanceof CloseWebSocketFrame) {
                // Handle WebSocket closure
            }
        }

        @Override
        public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
            // Handle exceptions
            cause.printStackTrace();
            ctx.close();
        }
    }
}

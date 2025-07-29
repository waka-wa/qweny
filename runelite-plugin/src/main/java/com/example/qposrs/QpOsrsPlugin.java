package com.example.qposrs;

import com.google.gson.Gson;
import com.google.inject.Provides;
import java.util.ArrayList;
import java.util.List;
import javax.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.Client;
import net.runelite.api.NPC;
import net.runelite.api.coords.WorldPoint;
import net.runelite.client.config.Config;
import net.runelite.client.config.ConfigGroup;
import net.runelite.client.config.ConfigItem;
import net.runelite.client.config.ConfigSection;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.plugins.PluginManager;
import net.runelite.client.ui.overlay.OverlayManager;

@PluginDescriptor(
    name = "Qwen Plays OSRS",
    description = "Publishes visible objects to a ZeroMQ socket for Qwen‑Plays‑OSRS",
    tags = {"Qwen", "OSRS", "automation", "ZeroMQ"},
    enabledByDefault = false
)
@Slf4j
public class QpOsrsPlugin extends Plugin
{
    @Inject
    private Client client;

    private ZmqPublisher publisher;

    private final Gson gson = new Gson();

    @Provides
    QpOsrsConfig provideConfig(com.google.inject.Injector injector)
    {
        return injector.getInstance(QpOsrsConfig.class);
    }

    @Override
    protected void startUp() throws Exception
    {
        QpOsrsConfig config = provideConfig(getInjector());
        publisher = new ZmqPublisher("tcp://127.0.0.1:5555");
        publisher.start();
        log.info("QpOsrsPlugin started");
    }

    @Override
    protected void shutDown() throws Exception
    {
        if (publisher != null)
        {
            publisher.close();
            publisher = null;
        }
        log.info("QpOsrsPlugin stopped");
    }

    @Subscribe
    public void onGameTick(net.runelite.api.events.GameTick event)
    {
        if (publisher == null)
        {
            return;
        }
        List<ObjectInfo> objects = new ArrayList<>();
        // As a simple example, publish all NPCs on screen
        for (NPC npc : client.getNpcs())
        {
            WorldPoint wp = npc.getWorldLocation();
            if (wp == null)
            {
                continue;
            }
            int id = npc.getId();
            String name = npc.getName();
            // Bounding boxes require project->scene conversion; omitted for brevity
            ObjectInfo info = new ObjectInfo(id, name, "NPC", new int[]{0, 0, 0, 0}, wp.getPlane());
            objects.add(info);
        }
        String json = gson.toJson(objects);
        publisher.publish(json);
    }

    public static class ObjectInfo
    {
        public final int id;
        public final String name;
        public final String type;
        public final int[] bbox;
        public final int level;

        public ObjectInfo(int id, String name, String type, int[] bbox, int level)
        {
            this.id = id;
            this.name = name;
            this.type = type;
            this.bbox = bbox;
            this.level = level;
        }
    }
}

@ConfigGroup("qposrs")
interface QpOsrsConfig extends Config
{
    @ConfigSection(
        name = "QpOsrs Settings",
        description = "Settings for the Qwen Plays OSRS plugin",
        position = 0
    )
    String qpSection = "qposrsSection";

    @ConfigItem(
        keyName = "enabled",
        name = "Enable publishing",
        description = "Publish visible objects over ZeroMQ",
        position = 1,
        section = qpSection
    )
    default boolean enabled()
    {
        return true;
    }
}
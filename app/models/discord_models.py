"""Discord entegrasyon modelleri.

Discord bot baglantisi, komut, kanal
ve thread yonetimi icin veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class DiscordConnectionState(str, Enum):
    """Baglanti durumu."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    READY = "ready"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class DiscordPresenceStatus(str, Enum):
    """Durum gosterimi."""

    ONLINE = "online"
    IDLE = "idle"
    DND = "dnd"
    INVISIBLE = "invisible"
    OFFLINE = "offline"


class DiscordChannelType(str, Enum):
    """Kanal tipi."""

    TEXT = "text"
    VOICE = "voice"
    CATEGORY = "category"
    ANNOUNCEMENT = "announcement"
    STAGE = "stage"
    FORUM = "forum"
    DM = "dm"


class DiscordCommandOptionType(str, Enum):
    """Komut opsiyon tipi."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    USER = "user"
    CHANNEL = "channel"
    ROLE = "role"
    NUMBER = "number"
    ATTACHMENT = "attachment"


class DiscordThreadState(str, Enum):
    """Thread durumu."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    LOCKED = "locked"


class DiscordGuild(BaseModel):
    """Discord sunucu."""

    guild_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    discord_guild_id: str = ""
    name: str = ""
    member_count: int = 0
    owner_id: str = ""
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class DiscordChannel(BaseModel):
    """Discord kanal."""

    channel_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    discord_channel_id: str = ""
    guild_id: str = ""
    name: str = ""
    channel_type: DiscordChannelType = (
        DiscordChannelType.TEXT
    )
    topic: str = ""
    is_nsfw: bool = False
    position: int = 0


class DiscordSlashCommand(BaseModel):
    """Slash komut."""

    command_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    description: str = ""
    guild_id: str = ""
    options: list[dict] = Field(
        default_factory=list,
    )
    permissions: list[str] = Field(
        default_factory=list,
    )
    enabled: bool = True
    usage_count: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class DiscordMessage(BaseModel):
    """Discord mesaj."""

    message_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    discord_message_id: str = ""
    channel_id: str = ""
    guild_id: str = ""
    author_id: str = ""
    author_name: str = ""
    content: str = ""
    embeds: list[dict] = Field(
        default_factory=list,
    )
    attachments: list[dict] = Field(
        default_factory=list,
    )
    reactions: list[str] = Field(
        default_factory=list,
    )
    reply_to: str = ""
    is_bot: bool = False
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class DiscordThread(BaseModel):
    """Discord thread."""

    thread_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    discord_thread_id: str = ""
    parent_channel_id: str = ""
    guild_id: str = ""
    name: str = ""
    owner_id: str = ""
    state: DiscordThreadState = (
        DiscordThreadState.ACTIVE
    )
    message_count: int = 0
    member_count: int = 0
    auto_archive_minutes: int = 1440
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class DiscordEmbed(BaseModel):
    """Discord embed."""

    title: str = ""
    description: str = ""
    color: int = 0x5865F2
    url: str = ""
    author_name: str = ""
    author_icon: str = ""
    footer_text: str = ""
    thumbnail_url: str = ""
    image_url: str = ""
    fields: list[dict] = Field(
        default_factory=list,
    )
    timestamp: datetime | None = None


class DiscordSnapshot(BaseModel):
    """Discord durum snapshot."""

    snapshot_id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    connection_state: DiscordConnectionState = (
        DiscordConnectionState.DISCONNECTED
    )
    total_guilds: int = 0
    total_channels: int = 0
    total_commands: int = 0
    total_messages_sent: int = 0
    total_threads: int = 0
    total_errors: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )



class ComponentType(str, Enum):
    """Discord bilesen tipi (Components v2)."""

    ACTION_ROW = "action_row"
    BUTTON = "button"
    SELECT_MENU = "select_menu"
    TEXT_INPUT = "text_input"
    MODAL = "modal"
    FILE_BLOCK = "file_block"


class ButtonStyleDiscord(str, Enum):
    """Discord buton stili."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    LINK = "link"


class DiscordComponent(BaseModel):
    """Discord bilesen (Components v2)."""

    component_type: ComponentType = (
        ComponentType.BUTTON
    )
    custom_id: str = ""
    label: str = ""
    style: ButtonStyleDiscord = (
        ButtonStyleDiscord.PRIMARY
    )
    url: str = ""
    disabled: bool = False
    allowed_users: list[str] = Field(
        default_factory=list,
    )
    reusable: bool = False
    children: list["DiscordComponent"] = Field(
        default_factory=list,
    )


class ForumThreadCreate(BaseModel):
    """Forum thread olusturma."""

    channel_id: str = ""
    name: str = ""
    content: str = ""
    auto_archive_duration: int = 1440
    applied_tags: list[str] = Field(
        default_factory=list,
    )


class AckReactionOverride(BaseModel):
    """Kanal bazli onay tepkisi gecersiz kilma."""

    channel_id: str = ""
    emoji: str = "👍"
    enabled: bool = True

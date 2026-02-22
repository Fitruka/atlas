"""Slack entegrasyon modelleri.

Slack bot baglantisi, olay, blok
ve workspace yonetimi icin veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class SlackConnectionState(str, Enum):
    """Baglanti durumu."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


class SlackAuthType(str, Enum):
    """Kimlik dogrulama tipi."""

    BOT_TOKEN = "bot_token"
    OAUTH = "oauth"
    SOCKET_MODE = "socket_mode"


class SlackEventType(str, Enum):
    """Olay tipi."""

    MESSAGE = "message"
    APP_MENTION = "app_mention"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    FILE_SHARED = "file_shared"
    CHANNEL_CREATED = "channel_created"
    MEMBER_JOINED = "member_joined_channel"
    MEMBER_LEFT = "member_left_channel"
    APP_HOME_OPENED = "app_home_opened"
    COMMAND = "command"


class SlackChannelType(str, Enum):
    """Kanal tipi."""

    PUBLIC = "public"
    PRIVATE = "private"
    DM = "dm"
    GROUP_DM = "group_dm"
    THREAD = "thread"


class SlackBlockType(str, Enum):
    """Blok tipi."""

    SECTION = "section"
    DIVIDER = "divider"
    IMAGE = "image"
    ACTIONS = "actions"
    CONTEXT = "context"
    INPUT = "input"
    HEADER = "header"
    FILE = "file"


class SlackUserStatus(str, Enum):
    """Kullanici durumu."""

    ACTIVE = "active"
    AWAY = "away"
    DND = "dnd"
    OFFLINE = "offline"


class SlackWorkspace(BaseModel):
    """Slack workspace."""

    workspace_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    team_id: str = ""
    name: str = ""
    domain: str = ""
    is_active: bool = True
    bot_user_id: str = ""
    bot_token: str = ""
    channel_count: int = 0
    member_count: int = 0
    connected_at: datetime | None = None


class SlackChannel(BaseModel):
    """Slack kanal."""

    channel_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    slack_channel_id: str = ""
    workspace_id: str = ""
    name: str = ""
    channel_type: SlackChannelType = (
        SlackChannelType.PUBLIC
    )
    topic: str = ""
    purpose: str = ""
    member_count: int = 0
    is_archived: bool = False
    is_member: bool = False


class SlackUser(BaseModel):
    """Slack kullanici."""

    user_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    slack_user_id: str = ""
    workspace_id: str = ""
    name: str = ""
    display_name: str = ""
    email: str = ""
    is_bot: bool = False
    is_admin: bool = False
    status: SlackUserStatus = (
        SlackUserStatus.ACTIVE
    )
    timezone: str = ""


class SlackMessage(BaseModel):
    """Slack mesaj."""

    message_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    slack_ts: str = ""
    channel_id: str = ""
    workspace_id: str = ""
    user_id: str = ""
    text: str = ""
    blocks: list[dict] = Field(
        default_factory=list,
    )
    attachments: list[dict] = Field(
        default_factory=list,
    )
    thread_ts: str = ""
    reactions: list[dict] = Field(
        default_factory=list,
    )
    is_bot: bool = False
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class SlackEvent(BaseModel):
    """Slack olay."""

    event_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    event_type: SlackEventType = (
        SlackEventType.MESSAGE
    )
    workspace_id: str = ""
    channel_id: str = ""
    user_id: str = ""
    data: dict = Field(
        default_factory=dict,
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class SlackBlock(BaseModel):
    """Slack blok."""

    block_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    block_type: SlackBlockType = (
        SlackBlockType.SECTION
    )
    text: str = ""
    fields: list[dict] = Field(
        default_factory=list,
    )
    accessory: dict = Field(
        default_factory=dict,
    )
    elements: list[dict] = Field(
        default_factory=list,
    )


class SlackModal(BaseModel):
    """Slack modal."""

    modal_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    title: str = ""
    submit_label: str = "Gonder"
    close_label: str = "Iptal"
    blocks: list[dict] = Field(
        default_factory=list,
    )
    callback_id: str = ""
    private_metadata: str = ""


class SlackSnapshot(BaseModel):
    """Slack durum snapshot."""

    snapshot_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    connection_state: SlackConnectionState = (
        SlackConnectionState.DISCONNECTED
    )
    total_workspaces: int = 0
    total_channels: int = 0
    total_messages_sent: int = 0
    total_events: int = 0
    total_errors: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )



class SlackStreamState(str, Enum):
    """Slack akis durumu."""

    IDLE = "idle"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"


class SlackStreamSession(BaseModel):
    """Slack native streaming oturumu."""

    session_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    channel_id: str = ""
    thread_ts: str = ""
    stream_id: str = ""
    state: SlackStreamState = (
        SlackStreamState.IDLE
    )
    total_chunks: int = 0
    started_at: float = 0.0


class SlackAckReaction(BaseModel):
    """Kanal bazli onay tepkisi."""

    channel_id: str = ""
    reaction: str = "eyes"
    enabled: bool = True

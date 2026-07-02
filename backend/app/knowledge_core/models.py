"""
FHOS Knowledge Core
Semantic Knowledge Graph
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)

    node_type = Column(String(50), nullable=False, index=True)
    object_id = Column(Integer, nullable=False, index=True)

    title = Column(String(255))
    description = Column(Text)

    links = relationship(
        "KnowledgeLink",
        foreign_keys="KnowledgeLink.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )


class KnowledgeLink(Base):
    __tablename__ = "knowledge_links"

    id = Column(Integer, primary_key=True, index=True)

    source_node_id = Column(
        Integer,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_node_id = Column(
        Integer,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relation = Column(String(100), nullable=False)

    confidence = Column(Float, default=1.0)

    created_by = Column(String(50), default="system")

    source_node = relationship(
        "KnowledgeNode",
        foreign_keys=[source_node_id],
        back_populates="links",
    )

    target_node = relationship(
        "KnowledgeNode",
        foreign_keys=[target_node_id],
    )
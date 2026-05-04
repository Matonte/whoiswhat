from .extensions import db


class DatasetSchema(db.Model):
    """Stores evaluation criteria / dataset definition JSON (e.g. k_training_schema, full taxonomy graph)."""

    __tablename__ = "dataset_schemas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    version = db.Column(db.String(32))
    document_json = db.Column(db.Text, nullable=False)


class TaxonomyNode(db.Model):
    __tablename__ = "taxonomy_nodes"

    node_id = db.Column(db.String(16), primary_key=True)
    node_type = db.Column(db.String(32), nullable=False)
    label = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)


class TaxonomyEdge(db.Model):
    __tablename__ = "taxonomy_edges"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_node_id = db.Column(db.String(16), db.ForeignKey("taxonomy_nodes.node_id"), nullable=False)
    target_node_id = db.Column(db.String(16), db.ForeignKey("taxonomy_nodes.node_id"), nullable=False)
    relation = db.Column(db.String(64), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "source_node_id", "target_node_id", "relation", name="uq_taxonomy_edge_triple"
        ),
    )


class TrainingExample(db.Model):
    """Labeled training / evaluation rows per k_training_schema.json fields."""

    __tablename__ = "training_examples"

    example_id = db.Column(db.String(32), primary_key=True)
    subject_name = db.Column(db.String(256), nullable=False)
    subject_type = db.Column(db.String(64), nullable=False)
    source_universe = db.Column(db.String(256), nullable=False)
    classification_code = db.Column(db.String(8), nullable=False)
    classification_label = db.Column(db.String(64), nullable=False)
    awareness_failure_score = db.Column(db.Integer, nullable=False)
    intent_failure_score = db.Column(db.Integer, nullable=False)
    control_failure_score = db.Column(db.Integer, nullable=False)
    short_rationale = db.Column(db.Text, nullable=False)
    evidence_points = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "example_id": self.example_id,
            "subject_name": self.subject_name,
            "subject_type": self.subject_type,
            "source_universe": self.source_universe,
            "classification_code": self.classification_code,
            "classification_label": self.classification_label,
            "awareness_failure_score": self.awareness_failure_score,
            "intent_failure_score": self.intent_failure_score,
            "control_failure_score": self.control_failure_score,
            "short_rationale": self.short_rationale,
            "evidence_points": self.evidence_points,
            "notes": self.notes,
        }

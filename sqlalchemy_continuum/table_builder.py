import sqlalchemy as sa
from sqlalchemy_utils import table_name
from .builder import VersionedBuilder


class VersionedTableBuilder(VersionedBuilder):
    @property
    def table_name(self):
        return self.option('table_name') % table_name(self.model)

    @property
    def parent_columns(self):
        """
        Returns a list of parent table columns.
        """
        if self.option('inspect_column_order'):
            inspector = sa.inspect(self.model.metadata.bind)
            columns = inspector.get_columns(self.model.__table__.name)
            ordered_columns = []
            for column in columns:
                ordered_columns.append(
                    self.model.__table__.c[column['name']]
                )
            return ordered_columns
        else:
            return self.model.__table__.c.values()

    def build_reflected_columns(self):
        columns = []

        for column in self.parent_columns:
            # Make a copy of the column so that it does not point to wrong
            # table.
            column_copy = column.copy()
            # Remove unique constraints
            column_copy.unique = False
            if column_copy.name == self.option('version_column_name'):
                column_copy.primary_key = True
            columns.append(column_copy)
        return columns

    def build_version_column(self):
        return sa.Column(
            self.option('version_column_name'),
            sa.BigInteger,
            primary_key=True
        )

    @property
    def metadata(self):
        for base in self.model.__bases__:
            if hasattr(base, 'metadata'):
                return base.metadata

        raise Exception(
            'Unable to find base class with appropriate metadata extension'
        )

    def build_table(self, extends=None):
        items = []
        if extends is None:
            items.extend(self.build_reflected_columns())
            items.append(self.build_version_column())

        return sa.schema.Table(
            extends.name if extends is not None else self.table_name,
            self.metadata,
            *items,
            extend_existing=extends is not None
        )
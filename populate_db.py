from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catalog, Base, Item, User

engine = create_engine('sqlite:///itemscatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


catalog1 = Catalog(name="Football")
catalog2 = Catalog(name="Basketball")
catalog3 = Catalog(name="Frisbee")
catalog4 = Catalog(name="Snowboarding")
catalog5 = Catalog(name="Skating")


user1 = User(name="John")


session.add(catalog1)
session.add(catalog2)
session.add(catalog3)
session.add(catalog4)
session.add(catalog5)

session.add(user1)

session.commit()

item2 = Item(name="Snowboard",
             description="A member of the Nitro Quiver Series line, the Fusion is a powerful, all-mountain snowboard that is designed to ride it all. ",
             catalog=catalog4, user=user1)

session.add(item2)
session.commit()


item1 = Item(name="Goggles", description="Large and oversized goggle frames. You have more lens space and larger field of vision.",
             catalog=catalog3, user=user1)

session.add(item1)
session.commit()

item2 = Item(name="Basketball Hoop",
             description="Mounts to the wall into two studs 16 inches apart.",
             catalog=catalog2, user=user1)

session.add(item2)
session.commit()

item3 = Item(name="Frisbee",
             description="This disc is accessible for any skill level, easy to throw, durable, and comfortable.",
             catalog=catalog3, user=user1)

session.add(item3)
session.commit()

item4 = Item(name="Football",
             description="Machine-stitched for soft touch and high durability.",
             catalog=catalog1, user=user1)

session.add(item4)
session.commit()

item5 = Item(name="Net",
             description="Material: 24 Ply Polyethylene",
             catalog=catalog2, user=user1)

session.add(item5)
session.commit()

item5 = Item(name="Jacket",
             description="Warm Fabric: Professional water repellent coated, fuzzy lining and durable fabric with 2400 polyester fibre which guarantees the best heat retention. Relaxed-fit style with quick-dry material.",
             catalog=catalog5, user=user1)

session.add(item5)
session.commit()


print("Catalogs, user and items ADDED to the database.")

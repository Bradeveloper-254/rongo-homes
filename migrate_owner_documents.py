import os
import shutil

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "rongo_homes.settings"
)

django.setup()

from django.conf import settings
from accounts.models import User


PUBLIC_ROOT = os.path.abspath(settings.MEDIA_ROOT)
PRIVATE_ROOT = os.path.abspath(settings.PRIVATE_MEDIA_ROOT)


DOCUMENT_FIELDS = [
    "id_document",
    "ownership_document",
    "additional_document",
]


def safe_path(root, relative_path):
    """
    Resolve a stored relative path and make sure it
    cannot escape the specified root directory.
    """
    full_path = os.path.abspath(
        os.path.join(root, relative_path)
    )

    if os.path.commonpath([root, full_path]) != root:
        raise RuntimeError(
            f"Unsafe path detected: {relative_path}"
        )

    return full_path


migrated = 0
missing = 0
skipped = 0


for user in User.objects(role="owner"):

    changed = False

    for field_name in DOCUMENT_FIELDS:

        relative_path = getattr(user, field_name, None)

        if not relative_path:
            continue

        relative_path = str(relative_path).replace("\\", "/")

        public_path = safe_path(
            PUBLIC_ROOT,
            relative_path
        )

        private_path = safe_path(
            PRIVATE_ROOT,
            relative_path
        )

        if not os.path.isfile(public_path):
            if os.path.isfile(private_path):
                print(
                    f"SKIP - already private: "
                    f"{relative_path}"
                )
                skipped += 1
            else:
                print(
                    f"MISSING: "
                    f"{relative_path}"
                )
                missing += 1

            continue

        os.makedirs(
            os.path.dirname(private_path),
            exist_ok=True
        )

        shutil.copy2(
            public_path,
            private_path
        )

        if not os.path.isfile(private_path):
            raise RuntimeError(
                f"Copy verification failed: "
                f"{private_path}"
            )

        setattr(
            user,
            field_name,
            relative_path
        )

        changed = True

        print(
            f"COPIED: {relative_path}"
        )

    if changed:
        user.save()
        print(
            f"UPDATED USER: {user.email}"
        )


print()
print("Migration copy phase complete.")
print(f"Migrated: {migrated}")
print(f"Missing:  {missing}")
print(f"Skipped:  {skipped}")
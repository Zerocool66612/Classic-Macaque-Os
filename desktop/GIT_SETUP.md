# Separate Classic repository

The source folder is ready to become a standalone Git repository.

1. Create a new repository on GitHub, for example `macaque-classic`.
2. Choose the visibility you want. Private is a reasonable initial choice.
3. Leave README, license and .gitignore initialization unchecked; these source
   files already include documentation and ignore rules. No project license has
   been selected yet.
4. To have ChatGPT publish through its GitHub connection, provide the repository
   URL and allow that connection to access the new repository.

Alternatively, publish from this extracted source folder using your existing Git
credentials and author configuration:

    bash publish-github.sh https://github.com/YOUR-NAME/macaque-classic.git

The script requires an empty remote, never force-pushes, and refuses to change a
mismatched origin. It does not create the repository or configure authentication.
No GitHub tokens or passwords belong in the source directory or chat.

Status at packaging time: no separate Classic repository has been created or
uploaded by this assistant. The connected GitHub account did not expose a Classic
repository, and repository creation is not available through the connector.

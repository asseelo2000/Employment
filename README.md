### Git Workflow Instructions

Follow these steps to manage your branches and ensure proper synchronization with the main branch:

1. **Stage and Commit Changes**:
    ```bash
    git add .
    git commit -am "Your commit message"
    ```

2. **Switch to the Main Branch and Pull Updates**:
    ```bash
    git checkout main
    git pull origin main
    ```

3. **Merge Main into Your Feature Branch**:
    ```bash
    git checkout dev
    git merge main
    ```

4. **Push Your Feature Branch to the Remote Repository**:
    ```bash
    git push origin dev
    ```

Make sure to resolve any merge conflicts during the process and test your changes before pushing.
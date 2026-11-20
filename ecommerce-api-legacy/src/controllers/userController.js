const { Messages } = require('../constants');

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            await userService.deleteUser(req.params.id);
            res.send(Messages.USER_DELETED);
        },
    };
}

module.exports = { createUserController };

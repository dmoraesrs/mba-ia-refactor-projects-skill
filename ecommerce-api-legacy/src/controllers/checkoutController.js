const { Messages } = require('../constants');
const { parseCheckoutInput } = require('./validators');

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const { enrollmentId } = await checkoutService.checkout(parseCheckoutInput(req.body));
            res.status(200).json({ msg: Messages.CHECKOUT_SUCCESS, enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };

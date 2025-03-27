var userInfo = context.getVariable("UserCalloutResponse.content");
if (!userInfo) {
    context.setVariable("userId", "");
} else {
    try {
        var user = JSON.parse(userInfo);
        context.setVariable("userId", user.userId || "");
        context.setVariable("external-organization-type", "UNITY");
    } catch (e) {
        context.setVariable("userId", "");
        context.setVariable("external-organization-type", "");
        print("Error extracting user info: " + e);
    }
}
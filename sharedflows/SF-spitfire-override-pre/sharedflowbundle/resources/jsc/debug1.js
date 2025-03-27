var debugInfo = context.getVariable("UserCalloutResponse.content");
var statusCode =  context.getVariable("UserCalloutResponse.status.code");
context.setVariable("DEBUG_CONTENT", JSON.stringify(debugInfo) || "NA");
context.setVariable("DEBUG_STATUS_CODE", statusCode || "NA");
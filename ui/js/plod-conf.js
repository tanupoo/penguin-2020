
const plod_locale = "ja";

/* header columns of listview */
const headers_base = [
    {
        "key": "publisher",
        "list": true,
        "notation": "所轄の自治体名",
        "orderable": true
    },
    {
        "key": "localId",
        "list": true,
        "notation": "管理No.",
        "orderable": true
    },
    {
        "key": "localSubId",
        "list": true,
        "notation": "副管理No.",
        "orderable": true
    },
    {
        "key": "dateConfirmed",
        "list": false,
        "notation": "患者の状態が確認された日付",
        "orderable": true
    },
    {
        "key": "disease",
        "list": true,
        "notation": "患者の病名",
        "orderable": true
    },
    {
        "key": "age",
        "list": true,
        "notation": "患者の年代",
        "orderable": true
    },
    {
        "key": "gender",
        "list": true,
        "notation": "患者の性別",
        "orderable": true
    },
    {
        "key": "residence",
        "list": true,
        "notation": "患者の居住地域",
        "orderable": true
    },
    {
        "key": "closeContacts",
        "list": false,
        "notation": "濃厚接触者情報",
        "orderable": false
    },
    {
        "key": "reportId",
        "list": true,
        "notation": "reportId",
        "orderable": false
    },
];

const headers_PLH = [
    { "key": "departureDate", "list": true, "notation": "出発日" },
    { "key": "departureTime", "list": true, "notation": "出発時間" },
    { "key": "departureFrom", "list": true, "notation": "出発地" },
    { "key": "departureFromAnnex", "list": true, "notation": "" },
    { "key": "arrivalDate", "list": true, "notation": "到着日" },
    { "key": "arrivalTime", "list": true, "notation": "到着時間" },
    { "key": "arrivalIn", "list": true, "notation": "到着地" },
    { "key": "arrivalInAnnex", "list": true, "notation": "" },
    { "key": "vehicles", "list": true, "notation": "移動方法(複数選択可)" },
    { "key": "vehicleOthers", "list": true, "notation": "" },
    { "key": "details", "list": true, "notation": "所見や患者の行動等" },
];

const headers_PCH = [
    "conditionDate",
    "conditionTime",
    "conditions",
    "conditionOthers",
    "details",
];

/* age */
const ageList = [
    { "key":"0-9",  "value":"0s" },
    { "key":"10代", "value":"10s" },
    { "key":"20代", "value":"20s" },
    { "key":"30代", "value":"30s" },
    { "key":"40代", "value":"40s" },
    { "key":"50代", "value":"50s" },
    { "key":"60代", "value":"60s" },
    { "key":"70代", "value":"70s" },
    { "key":"80代", "value":"80s" },
    { "key":"90代", "value":"90s" },
    { "key":"不明", "value":"Unspecified" },
];

/* gender */
const genderList = [
    { "key":"男性", "value":"Male" },
    { "key":"女性", "value":"Female" },
    { "key":"不明", "value":"Unspecified" },
];

/* disease */
const diseaseList = [
    { "key":"新型コロナウイルス", "value":"COVID-2019" },
    { "key":"麻疹", "value":"Measles" },
    { "key":"その他", "value":"Other" },
];

/* patientCondition + name */
const patientConditionList = [
    { "text": "倦怠感", "id": "Malaise" },
    { "text": "喀痰", "id": "Sputum" },
    { "text": "発熱", "id": "Fever" },
    { "text": "悪寒", "id": "Chill" },
    { "text": "咳", "id": "Cough" },
    { "text": "鼻水", "id": "RunnyNose" },
    { "text": "肺炎", "id": "Pneumonia" },
    { "text": "陽性", "id": "Positive" },
    { "text": "陰性", "id": "Negative" },
    { "text": "入院", "id": "Hospitalized" },
    { "text": "退院", "id": "Discharge" },
];

/* vehicles + name */
const vehiclesList = [
    { "text": "タクシー", "id": "Taxi" },
    { "text": "バス", "id": "Bus" },
    { "text": "電車", "id": "Train" },
    { "text": "飛行機", "id": "Airplane" },
    { "text": "船", "id": "Ship" },
    { "text": "徒歩", "id": "Walk" },
    { "text": "不明", "id": "Unknown" },
    // any vehicles that you can drive solely are not in case.
    // { "key": "自家用車・自転車・バイク", "name": "Bike" },
];

const DEFAULT_PLOD = {
    "publisher": "厚労省",
    "publisherOthers": "",
    "localId": "",
    "localSubId": "",
    "disease": "COVID-2019",
    "diseaseOthers": "",
    "dateConfirmed": "",
    "age": "Unspecified",
    "gender": "Unspecified",
    "residence": "Unspecified",
    "residenceAnnex": "",
    "closeContacts": "",
    "locationHistory": [
    ],
    "conditionHistory": [
    ],
};

const M_PLACEHOLDER_SELECT_OTHER_AND_INPUT = "選択肢にない場合、その他を選んでから記述する。";
const M_PLACEHOLDER_LOCATION_ANNEX = "建物名や駅名等、補足情報等があれば入力する。";
const M_PLACEHOLDER_TIME = "可能ならば時刻を入力する。";
const M_PLACEHOLDER_VEHICLE_TEXT = "自由記述\n(自家用車、バイク等他人と遭遇せず単独行動した場合等)";
const M_PLACEHOLDER_PLH_ANNEX = "備考等自由記述";
const M_PLACEHOLDER_PCH_ANNEX = "所見、患者の健康状態、検査機関、その他";
const M_PLACEHOLDER_LOCALID = "厚労省で管理している識別子等あれば入力する。";
const M_PLACEHOLDER_LOCALSUBID = "所轄における識別子等あれば入力する。";
const M_PLACEHOLDER_RESIDENCEANNEX = "補足情報等があれば入力する。";
const M_PLACEHOLDER_CLOSECONTACTS = "濃厚接触者の情報を列挙する。記述方法は要検討。";

const M_BUTTON_DELETE_THIS = "←削除";
const M_BUTTON_ADD_ABOVE = "↑追加";

const M_CONFIRM_SUBMIT_DATA = "登録しますか？";
const M_CONFIRM_CANCEL_SUBMISSION = "取り消しますか？";
const M_CONFIRM_PLOD_FAILED_CREATION = " の登録に失敗しました。";
const M_CONFIRM_PLOD_FAILED_DELETION = " の削除に失敗しました。";
const M_CONFIRM_PLOD_CREATED = " が登録されました。";
const M_CONFIRM_PLOD_DELETED = " が削除されました。";
const M_CONFIRM_PLOD_ASK_DELETION = "削除しますか？";
const M_ALERT_SELECT_OTHERS_AND_INPUT = "その他のフィールドに値を入れる場合は、選択肢からその他を選択してください。";
const M_ALERT_SELECT_DATA = "データを選択してください。";

const SELECT_OPT_OTHER = { "id": "Other", "text": "その他" };
const SELECT_OPT_ABROAD = { "id": "Abroad", "text": "海外" };
const SELECT_OPT_UNSPECIFIED = { "id": "Unspecified", "text": "不明" };
const SELECT_OPT_JAPAN = { "id": "Japan", "text": "日本" };
const SELECT_OPT_MHLW = { "id": "厚労省", "text": "厚労省" };

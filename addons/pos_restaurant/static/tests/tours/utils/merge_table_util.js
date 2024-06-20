import * as FloorScreen from "@pos_restaurant/../tests/tours/utils/floor_screen_util";
import * as ProductScreenPos from "@point_of_sale/../tests/tours/utils/product_screen_util";
import * as ProductScreenResto from "@pos_restaurant/../tests/tours/utils/product_screen_util";

const ProductScreen = { ...ProductScreenPos, ...ProductScreenResto };

export function mergeTableHelpers(childName, parentName) {
    return [
        FloorScreen.clickTable(childName),
        ProductScreen.clickControlButtonMore(),
        ProductScreen.clickControlButton("Merge"),
        {
            content: `click the merge button`,
            trigger: 'i[aria-label="Merge"]',
            run: "click",
        },
        FloorScreen.clickTable(parentName),
        ProductScreen.back(),
        {
            content: `Verify table ${childName} is merged into table ${parentName}`,
            trigger: `div.table div.label:contains("${parentName}")`,
            run: () => {
                if ($(`div.table div.label:contains('${parentName}')`).length < 2) {
                    console.error("Tables aren't merged");
                }
            },
        },
    ];
}

export function checkMergeTableIsCancelHelpers() {
    return [
        {
            content: `Verify table 4 and 5 isn't merge anymore`,
            trigger: 'div.table div.label:contains("4")',
            run: () => {
                if ($("div.table div.label:contains('4')").length !== 1) {
                    console.error("Table is still merge");
                }
            },
        },
        {
            content: `Verify table 4 and 5 isn't merge anymore`,
            trigger: 'div.table div.label:contains("5")',
            run: () => {
                if ($("div.table div.label:contains('5')").length !== 1) {
                    console.error("Table is still merge");
                }
            },
        },
    ];
}
